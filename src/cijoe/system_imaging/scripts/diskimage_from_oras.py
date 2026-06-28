#!/usr/bin/env python3
"""
Create a disk image from an oras:// artifact
============================================

Materializes the qcow2 disk-image for system-imaging entries that declare an
``oras`` source, such as nosi guest-images published to an OCI registry::

    [system-imaging.images.ubuntu-2604-x86_64]
    oras.url = "oras://ghcr.io/safl/nosi/ubuntu-2604-headless@sha256:<digest>"
    disk.path = "{{ local.env.HOME }}/system_imaging/disk/ubuntu-2604-x86_64.qcow2"

oras artifacts have no stable download URL, so the reference is resolved with the
withcache oras adapter (the anonymous bearer-token flow) to a registry blob URL
plus an auth header. The blob is pulled with curl, which retries and resumes,
then decompressed and converted to the qcow2 at ``disk.path``. A withcache curl
shim, if one is configured in the environment, caches the transfer transparently.

The pull is skipped when the pinned image is already staged, keyed on the content
digest recorded in a stamp next to the qcow2; bumping the digest in the config
re-stages.

Restrict which images are built with a case-insensitive fnmatch ``pattern``::

    with:
      pattern: "ubuntu-2604*"

Retargetable: False
-------------------

This script only runs on the initiator; it writes to the local filesystem.
"""
import errno
import gzip
import logging as log
import tempfile
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path

from withcache import oras

from cijoe.qemu.wrapper import qemu_img


def add_args(parser: ArgumentParser):
    parser.add_argument("--pattern", type=str, help="Pattern for image names to build")


def _curl(cijoe, url: str, headers: dict, dst: Path):
    """Pull ``url`` to ``dst`` with curl; retries and resumes on failure."""

    hdrs = " ".join(f"-H '{key}: {val}'" for key, val in headers.items())
    err, _ = cijoe.run_local(
        f"curl -fL --retry 5 --retry-all-errors -C - {hdrs} -o {dst} '{url}'"
    )
    return err


def diskimage_from_oras(cijoe, image: dict):
    """Resolve the oras source, pull it, and convert it to the disk image"""

    if not (oras_src := image.get("oras", {})):
        return None  # not an oras-sourced image; nothing to do
    if not (url := oras_src.get("url")):
        log.error("missing .oras.url entry in configuration file")
        return errno.EINVAL

    if not (disk := image.get("disk", {})):
        log.error("missing .disk entry in configuration file")
        return errno.EINVAL
    disk_path = Path(disk.get("path"))

    # Skip when the pinned image is already staged; the content digest is kept in
    # a stamp next to the qcow2 and a digest bump in the config re-stages.
    digest = oras.parse_ref(url).digest
    stamp = Path(f"{disk_path}.digest")
    if (
        digest
        and disk_path.exists()
        and stamp.exists()
        and stamp.read_text().strip() == digest
    ):
        log.info(f"image already staged at {disk_path} ({digest}); skipping pull")
        return 0

    resolved = oras.resolve_ref(url)
    disk_path.parent.mkdir(parents=True, exist_ok=True)

    # Workdir on disk_path's filesystem; a /tmp overlay may be too small for the
    # decompressed image.
    with tempfile.TemporaryDirectory(dir=disk_path.parent) as workdir:
        blob = Path(workdir) / "image.blob"
        if err := _curl(cijoe, resolved.blob_url, dict(resolved.headers), blob):
            log.error(f"curl({resolved.blob_url}): failed")
            return err

        # gzip-compressed artifacts decompress sparsely (disk images are mostly
        # zeros); anything else is handed to the converter as-is.
        with open(blob, "rb") as peek:
            gzipped = peek.read(2) == b"\x1f\x8b"
        src, src_fmt = blob, ""
        if gzipped:
            src, src_fmt = Path(workdir) / "image.raw", "-f raw "
            block_size = 1 << 20
            zero_block = b"\0" * block_size
            with gzip.open(blob, "rb") as compressed, open(src, "wb") as out:
                while chunk := compressed.read(block_size):
                    if len(chunk) == block_size and chunk == zero_block:
                        out.seek(block_size, 1)
                    else:
                        out.write(chunk)
                out.truncate()
            blob.unlink(missing_ok=True)

        if err := qemu_img(cijoe, f"convert {src_fmt}{src} -O qcow2 {disk_path}")[0]:
            log.error(f"qemu-img convert({src} -> {disk_path}): failed")
            return err

    # Headroom for the guest; cloud-init growpart grows the rootfs at boot.
    if err := qemu_img(cijoe, f"resize {disk_path} +8G")[0]:
        log.error(f"qemu-img resize({disk_path}): failed")
        return err

    stamp.write_text(digest or "")
    qemu_img(cijoe, f"info {disk_path}")
    return 0


def main(args, cijoe):
    """Build disk images for system-imaging entries with an oras source"""

    pattern = getattr(args, "pattern", None) or "*"

    if not (images := cijoe.getconf("system-imaging.images", {})):
        log.error("missing: 'system-imaging.images' in configuration file")
        return errno.EINVAL

    built = 0
    for image_name, image in images.items():
        if not fnmatch(image_name.lower(), pattern.lower()):
            continue
        if not image.get("oras"):
            continue

        log.info(f"building oras image: {image_name}")
        if err := diskimage_from_oras(cijoe, image):
            log.error(f"diskimage_from_oras({image_name}): err({err})")
            return err
        built += 1

    if not built:
        log.info(f"no oras-sourced images matched pattern({pattern})")

    return 0
