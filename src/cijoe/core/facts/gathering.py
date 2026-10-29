"""
Gathering facts about a target: what it is and has, under 'targets.<target>',
in the same layout whatever its OS. gather() is the entry point, used by the
core.facts_gather script, and by the CLI for the initiator before a run's first
step; the functions it calls parse what each OS reports.
"""

import logging as log
import re

from cijoe.core.misc import powershell, sh
from cijoe.core.tools import check, family_of

SECTIONS = ["os", "kernel", "system", "pci", "nvme", "gpu", "nic"]


def os_release(text: str) -> dict:
    """The keys facts keep from os-release(5) text, lower-cased"""

    values = {}
    for line in text.splitlines():
        match = re.match(r"([A-Z_]+)=(.*)", line.strip())
        if match:
            values[match.group(1).lower()] = match.group(2).strip().strip("\"'")

    return {
        k: values[k] for k in ["id", "version_id", "name", "pretty_name"] if k in values
    }


def uname(text: str) -> dict:
    """'uname -s -r -m' as kernel facts"""

    fields = text.split()
    if len(fields) < 3:
        return {}

    return {"name": fields[0], "release": fields[1], "machine": fields[2]}


# The NVMe namespaces of a Linux target, with their sysfs paths and nsids, read
# from sysfs or, on a kernel without the attribute, nvme-cli; each subsystem's
# controllers; and each controller's serial
LINUX_NVME = (
    "for p in /sys/class/block/nvme* /sys/class/nvme-generic/ng*; do"
    ' [ -e "$p" ] || continue; n=$(basename $p);'
    " case $n in *c*n*|*p[0-9]*) continue;; esac;"
    " i=$(cat $p/nsid 2>/dev/null"
    ' || nvme get-ns-id /dev/$n 2>/dev/null | sed "s/.*://");'
    ' echo "ns $n $(readlink -f $p) $i";'
    " done;"
    " for s in /sys/class/nvme-subsystem/*; do for c in $s/nvme[0-9]*; do"
    ' [ -e "$c" ] && echo "subsys $(basename $s) $(readlink -f $c)";'
    " done; done;"
    " for c in /sys/class/nvme/nvme*; do"
    ' [ -e "$c" ] && echo "ctrl $(readlink -f $c) $(cat $c/serial)";'
    " done; true"
)

CTRL_PATH = re.compile(
    r"/([0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7])/nvme/(nvme\d+)(/|$)"
)


def linux_nvme(listing: str) -> dict:
    """
    The controllers of LINUX_NVME's output, by name: each with its 'bdf',
    'serial' and 'namespaces', '{nsid, bdev, cdev}', a namespace of a shared
    subsystem under each of the subsystem's controllers
    """

    ctrls: dict = {}
    by_subsys: dict = {}
    namespaces = []
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0] == "ctrl":
            match = CTRL_PATH.search(fields[1])
            if match:
                bdf, name = match.groups()[:2]
                ctrls.setdefault(name, {"bdf": bdf, "namespaces": {}})
                ctrls[name]["serial"] = fields[2]
        elif len(fields) >= 3 and fields[0] == "subsys":
            match = CTRL_PATH.search(fields[2])
            if match:
                by_subsys.setdefault(fields[1], []).append(match.groups()[:2])
        elif len(fields) >= 3 and fields[0] == "ns":
            nsid = int(fields[3]) if len(fields) > 3 and fields[3].isdigit() else None
            namespaces.append((fields[1], fields[2], nsid))

    def entry(bdf, name, nsid, dev):
        # Without an nsid, a namespace's block and char devices pair by name,
        # nvme0n2 with ng0n2, so the namespaces stay apart
        ctrls.setdefault(name, {"bdf": bdf, "namespaces": {}})
        key = nsid if nsid is not None else re.sub(r"^(nvme|ng)\d+", "", dev)
        return ctrls[name]["namespaces"].setdefault(
            key, {"nsid": nsid} if nsid is not None else {}
        )

    for dev, path, nsid in namespaces:
        kind = "cdev" if dev.startswith("ng") else "bdev"
        match = CTRL_PATH.search(path)
        if match:
            bdf, name = match.group(1), match.group(2)
            entry(bdf, name, nsid, dev)[kind] = f"/dev/{dev}"
            continue
        subsys = re.search(r"/nvme-subsystem/(nvme-subsys\d+)/", path)
        for bdf, name in by_subsys.get(subsys.group(1), []) if subsys else []:
            entry(bdf, name, nsid, dev)[kind] = f"/dev/{dev}"

    for ctrl in ctrls.values():
        ctrl["namespaces"] = sorted(
            ctrl["namespaces"].values(), key=lambda n: (n.get("nsid") or 0)
        )

    return ctrls


LINUX_PCI = (
    "for d in /sys/bus/pci/devices/*; do [ -e $d/vendor ] || continue;"
    " echo $(basename $d) $(cat $d/vendor) $(cat $d/device) $(cat $d/class)"
    " $(basename $(readlink $d/driver) 2>/dev/null); done; true"
)


BDF = re.compile(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]")


def linux_pci(listing: str) -> list:
    """The PCI functions of LINUX_PCI's output, ordered by BDF"""

    functions = []
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) >= 4 and BDF.fullmatch(fields[0]):
            function = {
                "bdf": fields[0],
                "vendor": fields[1],
                "device": fields[2],
                "class": fields[3],
            }
            if len(fields) > 4:
                function["driver"] = fields[4]
            functions.append(function)

    return sorted(functions, key=lambda f: f["bdf"])


# What the kernel made of a Linux target's PCI functions: their DRM render
# nodes, network interfaces and RDMA devices
LINUX_PCI_DEVICES = (
    "for d in /sys/bus/pci/devices/*; do b=$(basename $d);"
    " for x in $d/drm/renderD*; do [ -e $x ] && echo render $b $(basename $x); done;"
    " for x in $d/net/*; do [ -e $x ] && echo netdev $b $(basename $x); done;"
    " for x in $d/infiniband/*; do [ -e $x ] && echo rdma $b $(basename $x); done;"
    " done; true"
)

# PCI base classes, the first byte of 'class': network, display, accelerator
NIC_CLASSES = ("02",)
GPU_CLASSES = ("03", "12")


def base_class(function: dict) -> str:
    return function["class"][2:4]


def linux_pci_devices(pci: list, listing: str, section: str) -> list:
    """The GPUs, section 'gpu', or NICs, 'nic', of 'pci', a linux_pci() list,
    each with what LINUX_PCI_DEVICES' output says the kernel made of it"""

    found: dict = {}
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] in ("render", "netdev", "rdma"):
            found.setdefault(fields[1], {}).setdefault(fields[0], []).append(
                fields[2] if fields[0] != "render" else f"/dev/dri/{fields[2]}"
            )

    devices = []
    for function in pci:
        made = found.get(function["bdf"], {})
        if section == "gpu" and base_class(function) in GPU_CLASSES:
            devices.append({**function, "render": sorted(made.get("render", []))})
        elif section == "nic" and base_class(function) in NIC_CLASSES:
            devices.append(
                {
                    **function,
                    "netdevs": sorted(made.get("netdev", [])),
                    "rdma": sorted(made.get("rdma", [])),
                }
            )

    return devices


def freebsd_pci_devices(pci: list, section: str) -> list:
    """The GPUs, section 'gpu', or NICs, 'nic', of 'pci', a freebsd_pci() list;
    a NIC's netdev is the name its driver gave it"""

    devices = []
    for function in pci:
        if section == "gpu" and base_class(function) in GPU_CLASSES:
            devices.append(dict(function))
        elif section == "nic" and base_class(function) in NIC_CLASSES:
            netdevs = [function["name"]] if "name" in function else []
            devices.append({**function, "netdevs": netdevs})

    return devices


FREEBSD_NVME = (
    "pciconf -l; camcontrol devlist -v; nvmecontrol devlist;"
    ' for c in $(pciconf -l | sed -n "s/^\\(nvme[0-9]*\\)@.*/\\1/p"); do'
    ' echo "ctrl $c $(nvmecontrol identify $c | sed -n "s/^Serial Number: *//p")";'
    " done"
)

PCICONF = re.compile(
    r"(\w+?)(\d+)@pci(\d+):(\d+):(\d+):(\d+):\s+class=(0x[0-9a-f]+)"
    r".*?vendor=(0x[0-9a-f]+) device=(0x[0-9a-f]+)"
)


def pciconf_bdf(dom, bus, slot, func) -> str:
    """A BDF from pciconf's decimal 'pci<domain>:<bus>:<slot>:<function>'"""

    return f"{int(dom):04x}:{int(bus):02x}:{int(slot):02x}.{int(func)}"


def freebsd_pci(listing: str) -> list:
    """The PCI functions of 'pciconf -l' output, ordered by BDF, each with the
    'name' its driver gave it, such as vtnet0; a function without a driver is
    'none<n>' there, and has no 'driver' or 'name' here"""

    functions = []
    for line in listing.splitlines():
        match = PCICONF.match(line)
        if not match:
            continue
        driver, unit, dom, bus, slot, func, cls, vendor, device = match.groups()
        function = {
            "bdf": pciconf_bdf(dom, bus, slot, func),
            "vendor": vendor,
            "device": device,
            "class": cls[:8],
        }
        if driver != "none":
            function["driver"] = driver
            function["name"] = f"{driver}{unit}"
        functions.append(function)

    return sorted(functions, key=lambda f: f["bdf"])


def freebsd_nvme(listing: str) -> dict:
    """
    The controllers of FREEBSD_NVME's output, by name, as linux_nvme() gives
    them: a namespace's 'cdev' is its nvme<c>ns<n>, its 'bdev' the nda disk CAM
    made of it, absent where the target uses nvd
    """

    bdfs, disks, namespaces, serials = {}, {}, [], {}
    scbus = None
    for line in listing.splitlines():
        pci = re.match(r"(nvme\d+)@pci(\d+):(\d+):(\d+):(\d+):", line)
        bus = re.match(r"(scbus\d+) on (\w+) bus", line)
        disk = re.search(r" lun (\d+) \(.*\b(nda\d+)\b", line)
        ns = re.match(r"\s+((nvme\d+)ns(\d+))\b", line)
        ctrl = re.match(r"ctrl (nvme\d+) (\S+)", line)
        if ctrl:
            serials[ctrl.group(1)] = ctrl.group(2)
        elif pci:
            name, dom, pbus, slot, func = pci.groups()
            bdfs[name] = pciconf_bdf(dom, pbus, slot, func)
        elif bus:
            scbus = bus.group(2)
        elif disk and scbus:
            disks[(scbus, int(disk.group(1)))] = f"/dev/{disk.group(2)}"
        elif ns:
            namespaces.append((ns.group(2), int(ns.group(3)), f"/dev/{ns.group(1)}"))

    ctrls: dict = {name: {"bdf": bdf, "namespaces": []} for name, bdf in bdfs.items()}
    for name, nsid, cdev in namespaces:
        if name not in ctrls:
            continue
        found = {"nsid": nsid, "cdev": cdev}
        if (name, nsid) in disks:
            found["bdev"] = disks[(name, nsid)]
        ctrls[name]["namespaces"].append(found)
    for name, number in serials.items():
        if name in ctrls:
            ctrls[name]["serial"] = number

    return ctrls


WINDOWS_NVME = (
    'Get-Disk | ForEach-Object { "disk {0} {1}" -f $_.Number, $_.Location };'
    ' Get-PhysicalDisk | ForEach-Object { "serial {0} {1}" -f $_.DeviceId, $_.SerialNumber }'
)


def windows_nvme(listing: str) -> dict:
    """
    The disks of WINDOWS_NVME's output, by 'PhysicalDrive<n>', the name xNVMe
    and others open as '//./PhysicalDrive<n>': each with its 'serial', its
    'bdf' where its location reads 'Bus b : Device d : Function f', and its
    one namespace's 'bdev'. Windows names no controller.
    """

    disks: dict = {}
    for line in listing.splitlines():
        disk = re.match(r"disk (\d+) (.*)", line)
        serial = re.match(r"serial (\d+) (\S+)", line)
        if disk:
            name = f"PhysicalDrive{disk.group(1)}"
            entry = disks.setdefault(name, {})
            entry["namespaces"] = [{"bdev": f"//./{name}"}]
            pci = re.search(r"Bus (\d+) : Device (\d+) : Function (\d+)", disk.group(2))
            if pci:
                b, d, f = (int(n) for n in pci.groups())
                entry["bdf"] = f"0000:{b:02x}:{d:02x}.{f}"
        elif serial:
            disks.setdefault(f"PhysicalDrive{serial.group(1)}", {})["serial"] = (
                serial.group(2)
            )

    return disks


def windows_os(text: str) -> dict:
    """'Caption|Version|OSArchitecture' as os and kernel facts"""

    fields = text.strip().split("|")
    if len(fields) < 3:
        return {}

    return {
        "os": {
            "id": "windows",
            "version_id": fields[1],
            "name": fields[0],
            "pretty_name": fields[0],
        },
        "kernel": {"name": "Windows_NT", "release": fields[1], "machine": fields[2]},
    }


# The tools each section runs on a target of each OS family, beyond the shell's
# own; a section whose tools the target lacks is left out
SECTION_TOOLS = {
    ("linux", "kernel"): ["uname"],
    ("linux", "system"): ["getconf"],
    ("freebsd", "kernel"): ["uname"],
    ("freebsd", "system"): ["sysctl"],
    ("freebsd", "pci"): ["pciconf"],
    ("freebsd", "nvme"): ["pciconf", "camcontrol", "nvmecontrol"],
    ("freebsd", "gpu"): ["pciconf"],
    ("freebsd", "nic"): ["pciconf"],
    ("darwin", "os"): ["sw_vers"],
    ("darwin", "kernel"): ["uname"],
    ("darwin", "system"): ["sysctl"],
    **{("windows", s): ["powershell"] for s in ("os", "kernel", "system", "nvme")},
}


def gather_section(cijoe, target, family: str, section: str):
    """The facts of 'section' on 'target', or None when the family has no way of
    gathering them here"""

    def run(command):
        err, state = cijoe.run(command, target=target)
        return None if err else state.output()

    def ints(**values):
        return {k: int(v) for k, v in values.items() if v and v.strip().isdigit()}

    if family in ("linux", "freebsd") and section == "os":
        text = run("cat /etc/os-release")
        return os_release(text) if text else None
    if family == "darwin" and section == "os":
        version = run("sw_vers -productVersion")
        name = run("sw_vers -productName")
        if not (version and name):
            return None
        return {
            "id": "macos",
            "version_id": version.strip(),
            "name": name.strip(),
            "pretty_name": f"{name.strip()} {version.strip()}",
        }
    if family in ("linux", "freebsd", "darwin") and section == "kernel":
        text = run("uname -s -r -m")
        return uname(text) if text else None
    if family == "linux" and section == "system":
        cpus = run("getconf _NPROCESSORS_ONLN")
        mem = run(sh("sed -n 's/^MemTotal: *\\([0-9]*\\) kB/\\1/p' /proc/meminfo"))
        return ints(cpus=cpus, memory_kib=mem)
    if family in ("freebsd", "darwin") and section == "system":
        cpus = run("sysctl -n hw.ncpu")
        mem = run(
            "sysctl -n " + ("hw.physmem" if family == "freebsd" else "hw.memsize")
        )
        facts = ints(cpus=cpus)
        if mem and mem.strip().isdigit():
            facts["memory_kib"] = int(mem.strip()) // 1024
        return facts
    if family == "linux" and section == "pci":
        text = run(sh(LINUX_PCI))
        return linux_pci(text) if text is not None else None
    if family == "freebsd" and section == "pci":
        text = run("pciconf -l")
        return freebsd_pci(text) if text is not None else None
    if family == "linux" and section in ("gpu", "nic"):
        pci, devices = run(sh(LINUX_PCI)), run(sh(LINUX_PCI_DEVICES))
        if pci is None or devices is None:
            return None
        return linux_pci_devices(linux_pci(pci), devices, section)
    if family == "freebsd" and section in ("gpu", "nic"):
        text = run("pciconf -l")
        return (
            freebsd_pci_devices(freebsd_pci(text), section)
            if text is not None
            else None
        )
    if family == "linux" and section == "nvme":
        text = run(sh(LINUX_NVME))
        return linux_nvme(text) if text is not None else None
    if family == "freebsd" and section == "nvme":
        text = run(sh(FREEBSD_NVME))
        return freebsd_nvme(text) if text is not None else None
    if family == "windows" and section in ("os", "kernel"):
        text = run(
            powershell(
                "$o = Get-CimInstance Win32_OperatingSystem;"
                ' "{0}|{1}|{2}" -f $o.Caption, $o.Version, $o.OSArchitecture'
            )
        )
        return windows_os(text).get(section) if text else None
    if family == "windows" and section == "system":
        text = run(
            powershell(
                "$s = Get-CimInstance Win32_ComputerSystem;"
                ' "{0} {1}" -f $s.NumberOfLogicalProcessors, $s.TotalPhysicalMemory'
            )
        )
        fields = (text or "").split()
        if len(fields) < 2 or not all(f.isdigit() for f in fields):
            return None
        return {"cpus": int(fields[0]), "memory_kib": int(fields[1]) // 1024}
    if family == "windows" and section == "nvme":
        text = run(powershell(WINDOWS_NVME))
        return windows_nvme(text) if text is not None else None

    return None


def gather(cijoe, target: str, sections: list) -> str:
    """Gather 'sections' about 'target' into its facts, each whose tools the
    target has; its OS family, or '' when it answers neither 'uname -s' nor
    PowerShell, and nothing is gathered"""

    facts = cijoe.facts.target(target)

    family = family_of(cijoe, target)
    if not family:
        return ""
    facts.update("os", {"family": family})

    for section in sections:
        tools = SECTION_TOOLS.get((family, section), [])
        lacking = check(cijoe, target, {tool: None for tool in tools})
        if lacking:
            log.info(
                f"target({target}): no {section} facts, lacking {', '.join(lacking)}"
            )
            continue
        gathered = gather_section(cijoe, target, family, section)
        if gathered is None:
            log.info(f"target({target}): no {section} facts gathered on {family}")
            continue
        if section == "os":
            gathered = {"family": family, **gathered}
        facts.set(section, gathered)

    return family
