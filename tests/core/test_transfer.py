import filecmp
import os
import tempfile

from cijoe.core.misc import ENCODING


def test_push_pull(cijoe):
    """Create a file, fill it, push it, pull it, and compare"""

    with tempfile.NamedTemporaryFile(
        encoding=ENCODING, mode="a", delete=False
    ) as test_file:
        test_file.write("".join([chr(65 + (i % 24)) for i in range(4096)]))
        test_file.flush()

        assert cijoe.put(test_file.name, "foo"), "Failed push()"

        assert cijoe.get("foo", "bar"), "Failed pull()"

        pulled = os.path.join(cijoe.output_path, cijoe.output_ident, "bar")

        assert filecmp.cmp(test_file.name, pulled, shallow=False), "Failed cmp()"
