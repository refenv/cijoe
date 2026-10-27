"""
Gather facts about a target
===========================

Records what a target is and has under 'targets.<target>' in the facts: its
operating system, kernel, CPUs and memory, PCI functions and NVMe controllers.
The target is reached through its transport, so it may be a QEMU guest or
hardware alike, and the facts have the same layout whatever its OS:

* os: family, id, version_id, name, pretty_name
* kernel: name, release, machine
* system: cpus, memory_kib
* pci: a list of bdf, vendor, device, class, driver, by bdf; a list, as a
  bdf has a dot, which a dotted key cannot hold
* nvme.<controller>: bdf, serial, namespaces [{nsid, bdev, cdev}]

The OS is found by probing the target, 'uname -s', or PowerShell where there is
no 'uname'. A section the target's OS has no way of gathering here is left out,
with a log line, so one task gathers what each target offers; a section that
was gathered and found nothing, such as no NVMe controllers, is empty. Other packages
add sections of their own the same way, with cijoe.facts.target().set().

A task reads the facts as '{{ target.os.id }}', for the default target, or as
'{{ facts.targets.<name>.os.id }}'.

Retargetable: True
------------------
"""

import errno
import logging as log
import re
from argparse import ArgumentParser

from cijoe.core.misc import powershell, sh
from cijoe.core.tools import family_of

SECTIONS = ["os", "kernel", "system", "pci", "nvme"]


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--target_name",
        type=str,
        default=None,
        help="The transport of the target to gather facts about; default: cijoe's.",
    )
    parser.add_argument(
        "--sections",
        type=str,
        default=",".join(SECTIONS),
        help=f"Comma-separated sections to gather; default: {','.join(SECTIONS)}.",
    )


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
    """The PCI functions of 'pciconf -l' output, ordered by BDF; a function
    without a driver is 'none<n>' there, and has no 'driver' here"""

    functions = []
    for line in listing.splitlines():
        match = PCICONF.match(line)
        if not match:
            continue
        driver, _, dom, bus, slot, func, cls, vendor, device = match.groups()
        function = {
            "bdf": pciconf_bdf(dom, bus, slot, func),
            "vendor": vendor,
            "device": device,
            "class": cls[:8],
        }
        if driver != "none":
            function["driver"] = driver
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


def gather_section(cijoe, target, family: str, section: str):
    """The facts of 'section' on 'target', or None when the family has no way of
    gathering them here"""

    def run(command):
        err, state = cijoe.run(command, transport_name=target)
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


def main(args, cijoe):
    """Gather the facts about the target"""

    target = args.target_name or cijoe.default_target
    if target not in cijoe.transports:
        log.error(f"no target({target}); known: {', '.join(cijoe.transports)}")
        return errno.EINVAL
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    unknown = [s for s in sections if s not in SECTIONS]
    if unknown:
        log.error(
            f"unknown sections({', '.join(unknown)}); known: {', '.join(SECTIONS)}"
        )
        return errno.EINVAL
    facts = cijoe.facts.target(target)

    family = family_of(cijoe, target)
    if not family:
        log.error(f"target({target}): neither 'uname -s' nor PowerShell answers")
        return errno.EIO
    facts.update("os", {"family": family})

    for section in sections:
        gathered = gather_section(cijoe, target, family, section)
        if gathered is None:
            log.info(f"target({target}): no {section} facts gathered on {family}")
            continue
        if section == "os":
            gathered = {"family": family, **gathered}
        facts.set(section, gathered)

    return 0
