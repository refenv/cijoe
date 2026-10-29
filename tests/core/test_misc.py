"""download(), download_and_verify() and decompress_file(), against a local server"""

import errno
import functools
import gzip
import hashlib
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from cijoe.core.misc import decompress_file, download, download_and_verify


@pytest.fixture
def served(tmp_path):
    """A directory served over http on localhost, and the URL it is served at"""

    root = tmp_path / "served"
    root.mkdir()
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield root, f"http://127.0.0.1:{server.server_address[1]}"

    server.shutdown()
    server.server_close()


def test_download(served, tmp_path):
    root, url = served
    (root / "file.txt").write_text("content")

    err, path = download(f"{url}/file.txt", tmp_path)
    assert err == 0
    assert path.read_text() == "content"


def test_download_of_a_missing_file_is_an_error(served, tmp_path):
    _, url = served

    err, _ = download(f"{url}/missing.txt", tmp_path)
    assert err == errno.EIO


def test_download_and_verify_without_its_checksums_is_an_error(served, tmp_path):
    root, url = served
    (root / "file.txt").write_text("content")

    err, _ = download_and_verify(
        f"{url}/file.txt", f"{url}/missing.sha256sum", tmp_path / "file.txt"
    )
    assert err
    assert not (tmp_path / "file.txt").exists()


def test_download_and_verify(served, tmp_path):
    root, url = served
    (root / "file.txt").write_text("content")
    digest = hashlib.sha256(b"content").hexdigest()
    (root / "file.sha256sum").write_text(f"{digest}  file.txt\n")

    err, path = download_and_verify(
        f"{url}/file.txt", f"{url}/file.sha256sum", tmp_path / "file.txt"
    )
    assert err == 0
    assert path.read_text() == "content"


def test_decompress_strips_only_the_file_suffix(tmp_path):
    folder = tmp_path / "images.gz.d"
    folder.mkdir()
    src = folder / "disk.img.gz"
    with gzip.open(src, "wb") as compressed:
        compressed.write(b"disk")

    err, dst = decompress_file(src)
    assert err == 0
    assert dst == folder / "disk.img"
    assert dst.read_bytes() == b"disk"
