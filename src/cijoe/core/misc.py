import errno
from pathlib import Path

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
