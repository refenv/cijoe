import subprocess

from cijoe.core.facts import Facts
from cijoe.core.scripts import facts_gather as gather

# What the listings printed on Linux, FreeBSD 14.4 and a Windows 11 guest
PCI = "/sys/devices/pci0000:00/0000:00:03.0"
LINUX_NVME = f"""\
ns nvme1n1 {PCI}/0000:01:00.0/nvme/nvme1/nvme1n1 1
ns ng1n1 {PCI}/0000:01:00.0/nvme/nvme1/ng1n1 1
ns ng0n1 /sys/devices/pci0000:00/0000:00:04.0/0000:02:00.0/nvme/nvme0/ng0n1 1
ns nvme2n1 /sys/devices/virtual/nvme-subsystem/nvme-subsys2/nvme2n1 1
ns ng2n1 /sys/devices/virtual/nvme-subsystem/nvme-subsys2/ng2n1
subsys nvme-subsys1 {PCI}/0000:01:00.0/nvme/nvme1
subsys nvme-subsys2 /sys/devices/pci0000:00/0000:00:05.0/0000:03:00.0/nvme/nvme2
ctrl {PCI}/0000:01:00.0/nvme/nvme1 beef0000
ctrl /sys/devices/pci0000:00/0000:00:05.0/0000:03:00.0/nvme/nvme2 beef0005
"""

FREEBSD_NVME = """\
hostb0@pci0:0:0:0:\tclass=0x060000 rev=0x00 hdr=0x00 vendor=0x8086 device=0x29c0
none0@pci0:0:31:3:\tclass=0x0c0500 rev=0x02 hdr=0x00 vendor=0x8086 device=0x2930
nvme0@pci0:1:0:0:\tclass=0x010802 rev=0x00 hdr=0x00 vendor=0x144d device=0xa80c
nvme1@pci0:10:0:0:\tclass=0x010802 rev=0x02 hdr=0x00 vendor=0x1b36 device=0x0010
scbus2 on ahcich2 bus 0:
<QEMU QEMU DVD-ROM 2.5+>           at scbus2 target 0 lun 0 (pass0,cd0)
scbus6 on nvme0 bus 0:
<Samsung SSD 990 PRO 2TB 5B2QJXD7>  at scbus6 target 0 lun 1 (pass1,nda0)
<>                                 at scbus6 target -1 lun ffffffff ()
 nvme0: Samsung SSD 990 PRO 2TB
    nvme0ns1 (1907729MB)
 nvme1: QEMU NVMe Ctrl
    nvme1ns1 (1024MB)
ctrl nvme0 S7HENU0Y551082W
ctrl nvme1 beef0001
"""

WINDOWS_NVME = """\
disk 0 PCI Slot 0 : Bus 0 : Device 31 : Function 2 : Adapter 0 : Port 0 : Target 0 : LUN 0
disk 1 PCI Slot 2 : Bus 1 : Device 0 : Function 0 : Adapter 0 : Port 0 : Target 0 : LUN 0
disk 2 Integrated : Adapter 0 : Port 0 : Target 0 : LUN 0
serial 1 S7HENU0Y551082W
"""


def test_os_release_and_uname():
    text = (
        'NAME="Ubuntu"\nVERSION_ID="26.04"\nID=ubuntu\nPRETTY_NAME="Ubuntu 26.04 LTS"\n'
    )
    assert gather.os_release(text) == {
        "id": "ubuntu",
        "version_id": "26.04",
        "name": "Ubuntu",
        "pretty_name": "Ubuntu 26.04 LTS",
    }
    assert gather.uname("FreeBSD 14.4-RELEASE-p6 amd64\n") == {
        "name": "FreeBSD",
        "release": "14.4-RELEASE-p6",
        "machine": "amd64",
    }
    assert gather.uname("") == {}


def test_linux_nvme_by_controller():
    ctrls = gather.linux_nvme(LINUX_NVME)

    assert ctrls["nvme1"] == {
        "bdf": "0000:01:00.0",
        "serial": "beef0000",
        "namespaces": [{"nsid": 1, "bdev": "/dev/nvme1n1", "cdev": "/dev/ng1n1"}],
    }
    assert ctrls["nvme0"] == {
        "bdf": "0000:02:00.0",
        "namespaces": [{"nsid": 1, "cdev": "/dev/ng0n1"}],
    }
    shared = ctrls["nvme2"]
    assert shared["serial"] == "beef0005"
    assert {"nsid": 1, "bdev": "/dev/nvme2n1"} in shared["namespaces"]
    assert {"cdev": "/dev/ng2n1"} in shared["namespaces"], "no nsid is left out"


def test_linux_pci_by_bdf():
    listing = (
        "0000:00:00.0 0x8086 0x29c0 0x060000\n"
        "0000:01:00.0 0x144d 0xa80c 0x010802 nvme\n"
        "not a function\n"
    )
    assert gather.linux_pci(listing) == [
        {
            "bdf": "0000:00:00.0",
            "vendor": "0x8086",
            "device": "0x29c0",
            "class": "0x060000",
        },
        {
            "bdf": "0000:01:00.0",
            "vendor": "0x144d",
            "device": "0xa80c",
            "class": "0x010802",
            "driver": "nvme",
        },
    ]


def test_freebsd_pci_and_nvme():
    pci = {f["bdf"]: f for f in gather.freebsd_pci(FREEBSD_NVME)}
    assert pci["0000:01:00.0"] == {
        "bdf": "0000:01:00.0",
        "vendor": "0x144d",
        "device": "0xa80c",
        "class": "0x010802",
        "driver": "nvme",
        "name": "nvme0",
    }
    assert "driver" not in pci["0000:00:1f.3"], "'none' is no driver"
    assert pci["0000:0a:00.0"]["vendor"] == "0x1b36", "pciconf's bus is decimal"
    assert list(pci) == sorted(pci), "ordered by bdf"

    assert gather.freebsd_nvme(FREEBSD_NVME) == {
        "nvme0": {
            "bdf": "0000:01:00.0",
            "serial": "S7HENU0Y551082W",
            "namespaces": [{"nsid": 1, "cdev": "/dev/nvme0ns1", "bdev": "/dev/nda0"}],
        },
        "nvme1": {
            "bdf": "0000:0a:00.0",
            "serial": "beef0001",
            "namespaces": [{"nsid": 1, "cdev": "/dev/nvme1ns1"}],
        },
    }


def test_windows_nvme_and_os():
    assert gather.windows_nvme(WINDOWS_NVME) == {
        "PhysicalDrive0": {
            "namespaces": [{"bdev": "//./PhysicalDrive0"}],
            "bdf": "0000:00:1f.2",
        },
        "PhysicalDrive1": {
            "namespaces": [{"bdev": "//./PhysicalDrive1"}],
            "bdf": "0000:01:00.0",
            "serial": "S7HENU0Y551082W",
        },
        "PhysicalDrive2": {"namespaces": [{"bdev": "//./PhysicalDrive2"}]},
    }
    found = gather.windows_os("Microsoft Windows 11 Pro|10.0.26100|64-bit\n")
    assert found["os"]["id"] == "windows" and found["kernel"]["release"] == "10.0.26100"


def test_listings_parse_as_shell():
    for listing in (gather.LINUX_NVME, gather.LINUX_PCI, gather.FREEBSD_NVME):
        subprocess.run(["sh", "-n", "-c", listing], check=True)


def test_linux_namespaces_without_nsid_stay_apart():
    listing = (
        f"ns nvme1n1 {PCI}/0000:01:00.0/nvme/nvme1/nvme1n1\n"
        f"ns ng1n1 {PCI}/0000:01:00.0/nvme/nvme1/ng1n1\n"
        f"ns nvme1n2 {PCI}/0000:01:00.0/nvme/nvme1/nvme1n2\n"
        f"ns ng1n2 {PCI}/0000:01:00.0/nvme/nvme1/ng1n2\n"
    )
    assert gather.linux_nvme(listing)["nvme1"]["namespaces"] == [
        {"bdev": "/dev/nvme1n1", "cdev": "/dev/ng1n1"},
        {"bdev": "/dev/nvme1n2", "cdev": "/dev/ng1n2"},
    ]


def test_powershell_needs_no_quoting():
    import base64

    command = '$o = Get-CimInstance Win32_OperatingSystem; "{0}|{1}" -f $o.Caption'
    words = gather.powershell(command).split()

    assert words[:4] == [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
    ]
    assert len(words) == 5, "one word, whatever the login shell"
    assert base64.b64decode(words[4]).decode("utf-16-le") == command


class Target:
    """A cijoe whose target answers each command with what 'answers' says"""

    class State:
        def __init__(self, text):
            self.text = text

        def output(self):
            return self.text

    def __init__(self, answers, tmp_path):
        self.answers = answers
        self.transports = {"initiator": None}
        self.default_target = "initiator"
        self.facts = Facts(tmp_path / "facts.toml")

    def getconf(self, key, default=None):
        return default

    def run(self, command, transport_name=None):
        for prefix, (err, text) in self.answers.items():
            if command.startswith(prefix):
                return err, Target.State(text)
        return 1, Target.State("")


def test_windows_with_msys_is_windows(tmp_path):
    target = Target({"uname -s": (0, "MINGW64_NT-10.0-26100\n")}, tmp_path)
    assert gather.family_of(target, "initiator") == "windows"

    target = Target({"powershell": (0, "7.4\n")}, tmp_path)
    assert gather.family_of(target, "initiator") == "windows"


def test_unknown_targets_and_sections_write_nothing(tmp_path):
    from argparse import Namespace

    target = Target({"uname -s": (0, "Linux\n")}, tmp_path)

    args = Namespace(target_name="nosuch", sections="os", skip="")
    assert gather.main(args, target) != 0
    args = Namespace(target_name=None, sections="os,nosuch", skip="")
    assert gather.main(args, target) != 0
    args = Namespace(target_name=None, sections="os", skip="nosuch")
    assert gather.main(args, target) != 0
    assert target.facts.data == {}


def test_gathering_from_a_named_task(tmp_path):
    # cijoe's own 'target' is the task file; the step's target is 'target_name'
    import yaml

    from cijoe.core.resources import dict_from_tomlfile

    task = {"doc": "Gather", "steps": [{"name": "gather", "uses": "core.facts_gather"}]}
    (tmp_path / "gather.yaml").write_text(yaml.dump(task))
    (tmp_path / "config.toml").write_text("")
    result = subprocess.run(
        ["cijoe", "gather.yaml", "-c", "config.toml", "-o", "out", "--report-skip"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    facts = dict_from_tomlfile(tmp_path / "out" / "facts.toml")
    assert facts["targets"]["initiator"]["kernel"]["release"]


LINUX_PCI_LISTING = """\
0000:00:00.0 0x8086 0x29c0 0x060000
0000:01:00.0 0x1b36 0x0010 0x010802 nvme
0000:04:00.0 0x1002 0x75c1 0x120000 amdgpu
0000:05:00.0 0x1af4 0x1041 0x020000 virtio-pci
0000:06:00.0 0x1dd8 0x1001 0x020000 rocm_ernic
"""

LINUX_DEVICES_LISTING = """\
render 0000:04:00.0 renderD128
netdev 0000:06:00.0 ernic0
rdma 0000:06:00.0 rocm_ernic0
"""


def test_linux_gpus_and_nics():
    pci = gather.linux_pci(LINUX_PCI_LISTING)

    assert gather.linux_pci_devices(pci, LINUX_DEVICES_LISTING, "gpu") == [
        {
            "bdf": "0000:04:00.0",
            "vendor": "0x1002",
            "device": "0x75c1",
            "class": "0x120000",
            "driver": "amdgpu",
            "render": ["/dev/dri/renderD128"],
        }
    ]
    nics = gather.linux_pci_devices(pci, LINUX_DEVICES_LISTING, "nic")
    assert [n["bdf"] for n in nics] == ["0000:05:00.0", "0000:06:00.0"]
    assert nics[0]["netdevs"] == [] and nics[0]["rdma"] == []
    assert nics[1]["netdevs"] == ["ernic0"] and nics[1]["rdma"] == ["rocm_ernic0"]


def test_freebsd_gpus_and_nics():
    listing = (
        "vgapci0@pci0:0:1:0:\tclass=0x030000 rev=0x02 hdr=0x00 vendor=0x1234 device=0x1111\n"
        "vtnet0@pci0:0:3:0:\tclass=0x020000 rev=0x00 hdr=0x00 vendor=0x1af4 device=0x1000\n"
        "none1@pci0:0:4:0:\tclass=0x020000 rev=0x00 hdr=0x00 vendor=0x8086 device=0x10d3\n"
    )
    pci = gather.freebsd_pci(listing)

    gpus = gather.freebsd_pci_devices(pci, "gpu")
    assert [(g["bdf"], g["driver"]) for g in gpus] == [("0000:00:01.0", "vgapci")]
    nics = gather.freebsd_pci_devices(pci, "nic")
    assert [(n["bdf"], n["netdevs"]) for n in nics] == [
        ("0000:00:03.0", ["vtnet0"]),
        ("0000:00:04.0", []),
    ]


def test_a_section_lacking_its_tools_is_left_out_and_skip_leaves_out(tmp_path):
    from argparse import Namespace

    answers = {
        "uname -s -r -m": (0, "Linux 6.12.1 x86_64\n"),
        "uname -s": (0, "Linux\n"),
        "uname --version": (0, "uname (GNU coreutils) 9.4\n"),
        "sh -c 'command -v uname'": (0, "/usr/bin/uname\n"),
        "sh -c 'command -v getconf'": (1, ""),
        "cat /etc/os-release": (0, "ID=debian\n"),
    }
    target = Target(answers, tmp_path)

    args = Namespace(target_name=None, sections="os,kernel,system", skip="os")
    assert gather.main(args, target) == 0
    facts = target.facts.get("targets.initiator")
    assert facts["kernel"]["release"] == "6.12.1"
    assert "system" not in facts, "getconf is lacking"
    assert facts["tools"]["getconf"] == {"name": "getconf", "found": False}
    assert facts["tools"]["uname"]["found"]
    assert facts["os"] == {"family": "linux"}, "os was skipped, its family kept"
