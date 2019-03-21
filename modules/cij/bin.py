"""
bin.py      - Script providing operation of buffer

Classes:
    Buffer.length()     - Get length of array
    Buffer.size()       - Get size of buffer
    Buffer.types()      - Get type of item
    Buffer.write()      - Write buffer to file
    Buffer.read()       - Read buffer from file
    Buffer.dump()       - Dump buffer item to console
    Buffer.compare()    - Compare two buffers

"""
# pylint: disable=E0012,R0205
from ctypes import c_uint8, memmove, sizeof, cast, POINTER, Structure, Union, Array
import cij


def dump(buf, indent=0, skip=""):
    """Dump UnionType/StructType to STDOUT"""
    if not isinstance(type(buf), (type(Union), type(Structure))):
        raise RuntimeError("Error type(%s)" % type(buf))

    for field in getattr(buf, '_fields_'):
        name, types = field[0], field[1]
        if name in skip:
            return
        value = getattr(buf, name)

        if isinstance(types, (type(Union), type(Structure))):
            cij.info("%s%s:" % (" " * indent, name))
            dump(value, indent+2, skip)
        elif isinstance(types, type(Array)):
            for i, item in enumerate(value):
                name_index = "%s[%s]" % (name, i)

                if isinstance(types, (type(Union), type(Structure))):
                    cij.info("%s%s:" % (" " * indent, name_index))
                    dump(item, indent + 2, skip)
                else:
                    cij.info("%s%-12s: 0x%x" % (" " * indent, name_index, item))
        else:
            cij.info("%s%-12s: 0x%x" % (" " * indent, name, value))


def compare(buf_a, buf_b, ignore):
    """Compare of two Buffer item"""
    for field in getattr(buf_a, '_fields_'):
        name, types = field[0], field[1]

        if name in ignore:
            continue

        val_a = getattr(buf_a, name)
        val_b = getattr(buf_b, name)

        if isinstance(types, (type(Union), type(Structure))):
            if compare(val_a, val_b, ignore):
                return 1
        elif isinstance(types, type(Array)):
            for i, _ in enumerate(val_a):
                if isinstance(types, (type(Union), type(Structure))):
                    if compare(val_a[i], val_b[i], ignore):
                        return 1
                else:
                    if val_a[i] != val_b[i]:
                        return 1
        else:
            if val_a != val_b:
                return 1

    return 0


class Buffer(object):
    """Ctypes operation"""

    def __init__(self, types=c_uint8, length=1):
        self.m_types = types
        self.m_len = length
        self.m_sizeof = sizeof(self.m_types)
        self.m_size = self.m_len * self.m_sizeof
        self.m_buf = (self.m_types * self.m_len)()

    def __getitem__(self, key):
        return self.m_buf[key]

    def __setitem__(self, key, val):
        self.m_buf[key] = val

    def length(self):
        """Get length of types"""

        return self.m_len

    def size(self):
        """Get size of buffer"""

        return self.m_size

    def types(self):
        """Get types of buffer"""

        return self.m_types

    def memcopy(self, stream, offset=0, length=float("inf")):
        """Copy stream to buffer"""
        data = [ord(i) for i in list(stream)]
        size = min(length, len(data), self.m_size)
        buff = cast(self.m_buf, POINTER(c_uint8))
        for i in range(size):
            buff[offset + i] = data[i]

    def write(self, path):
        """Write buffer to file"""

        with open(path, "wb") as fout:
            fout.write(self.m_buf)

    def read(self, path):
        """Read file to buffer"""

        with open(path, "rb") as fout:
            memmove(self.m_buf, fout.read(self.m_size), self.m_size)

    def dump(self, offset=0, length=1):
        """Dump item"""

        for i in range(offset, offset + length):
            if "ctypes" in str(self.m_types):
                cij.info("Buff[%s]: %s" % (i, self.m_buf[i]))
            else:
                cij.info("Buff[%s]:" % i)
                dump(self.m_buf[i], 2)

    def compare(self, buf, offset=0, length=1, ignore=""):
        """Compare buffer"""

        for i in range(offset, offset + length):
            if isinstance(self.m_types, (type(Union), type(Structure))):
                if compare(self.m_buf[i], buf[i], ignore=ignore):
                    return 1
            elif self.m_buf[i] != buf[i]:
                return 1

        return 0
