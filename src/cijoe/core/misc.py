import errno
import hashlib
import logging as log
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import requests

ENCODING = "UTF-8"


def sanitize_ident(ident: str):
    """Naive ident sanitizer"""

    for illegal in r'/\|!?[]<>.,:;"*':
        ident = ident.replace(illegal, "_")

    return ident


def download(url: str, path: Path):
    """Downloads a file over http(s), returns (err, path)."""

    path = Path(path).resolve()
    if path.is_dir():
        path = path / url.split("/")[-1]
    if not (path.parent.is_dir() and path.parent.exists()):
        return errno.EINVAL, path

    with requests.get(url, stream=True) as request:
        request.raise_for_status()
        with path.open("wb") as local:
            for chunk in request.iter_content(chunk_size=8192):
                local.write(chunk)

    return 0, path


def get_checksums_from_url(url_checksum: str):
    """
    Downloads checksum(s) from given url to a temporary directory, returns
    the hashing algorithm and the contents of the file. The algorithm is
    found based on the filename of the downloaded checksum file.
    Returns (err, checksums, algorithm).
    """

    dir = TemporaryDirectory()
    err, path_checksum = download(url_checksum, Path(dir.name).resolve())
    if err:
        log.error(f"download({url_checksum}), {path_checksum}: failed")
        return err, None, None

    with open(path_checksum, "r") as checksum_f:
        # Loop through valid hash algorithms to find the one that matches the
        # filename of the checksum
        for algorithm in hashlib.algorithms_guaranteed:
            if algorithm in path_checksum.name.lower():
                return 0, checksum_f.read(), algorithm

    log.error(
        "error: downloaded checksum does contain the name of a valid hash algorithm"
    )
    return 1, None, None


def download_and_verify(url: str, url_checksum: str, path: Path):
    """
    Downloads a file over http(s). The file is only downloaded if checksums are
    not equal and if the checksum at url_checksum matches the downloaded file,
    returns (err, path).
    """

    path = Path(path).resolve()
    if path.is_dir():
        path = path / url.split("/")[-1]
    if not (path.parent.is_dir() and path.parent.exists()):
        return errno.EINVAL, path

    err, verification, algorithm = get_checksums_from_url(url_checksum)
    if err:
        log.error(f"error when downloading checksum ({url_checksum})")

    # The checksum of the existing file at path
    checksum = None
    checksum_path = path.with_suffix(path.suffix + f".{algorithm}sum")
    if path.exists() and checksum_path.exists():
        with open(checksum_path, "r") as f:
            checksum = f.read()

    # If the file does not already exists or if checksums do not match,
    # download from url
    if not checksum or checksum not in verification:
        log.info(f"Downloading file from {url}")

        with NamedTemporaryFile() as dwnld:
            err, dwnld_path = download(url, Path(dwnld.name).resolve())
            if err:
                log.error(f"download({url}), {dwnld_path}: failed")
                return err, None

            # Check that downloaded checksum file contains the checksum of
            # the downloaded file
            new_checksum = hashlib.file_digest(dwnld, algorithm).hexdigest()
            if new_checksum not in verification:
                log.error(
                    f"error while downloading file: checksum ({new_checksum}) not in checksum file:\n{verification}"
                )
                return 1, None

            # Move contents of temporary file to the given path
            shutil.copyfile(dwnld_path, path)
            with open(checksum_path, "w") as f:
                f.write(new_checksum)

    return 0, path
