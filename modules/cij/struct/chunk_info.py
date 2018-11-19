"""
chunk_info.py     - Get Log Page, Chunk Information
"""

from ctypes import Structure, c_uint8, c_uint64, sizeof
# pylint: disable=locally-disabled, too-few-public-methods


class DescriptorTableSpec20(Structure):
    """Chunk Descriptor Table"""
    _pack_ = 1
    _fields_ = [
        ('CS', c_uint8),        # Chunk State
        ('CT', c_uint8),        # Chunk Type
        ('WL', c_uint8),        # Wear-level Index
        ('RSV0', c_uint8 * 5),
        ('SLBA', c_uint64),     # Starting LBA
        ('CNLB', c_uint64),     # Number of blocks in chunk
        ('WP', c_uint64),       # Write Pointer
    ]


class DescriptorTableDenali(Structure):
    """Chunk Descriptor Table"""
    _pack_ = 1
    _fields_ = [
        ('CS', c_uint8),        # Chunk State
        ('CT', c_uint8),        # Chunk Type
        ('WL', c_uint8),        # Wear-level Index
        ('RSV0', c_uint8 * 5),
        ('SLBA', c_uint64),     # Starting LBA
        ('CNLB', c_uint64),     # Number of blocks in chunk
        ('WP', c_uint64),       # Write Pointer
        ('ILBA', c_uint64),     # Number of invalid LBAs
        ('RSV1', c_uint64 * 3),
    ]


def get_descriptor_table(version="Denali"):
    """
    Get descriptor table by version(denali, spec20)
    """
    if version == "Denali":
        return DescriptorTableDenali
    elif version == "Spec20":
        return DescriptorTableSpec20
    elif version == "Spec12":
        return None
    else:
        raise RuntimeError("Error version!")


def get_sizeof_descriptor_table(version="Denali"):
    """
    Get sizeof DescriptorTable
    """
    if version == "Denali":
        return sizeof(DescriptorTableDenali)
    elif version == "Spec20":
        return sizeof(DescriptorTableSpec20)
    elif version == "Spec12":
        return 0
    else:
        raise RuntimeError("Error version!")
