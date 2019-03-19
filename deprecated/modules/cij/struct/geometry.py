"""
geometry.py     - Device Geometry Data Structure
"""

from ctypes import Structure, c_uint8, c_uint16, c_uint32
# pylint: disable=locally-disabled, too-few-public-methods


class LBAF(Structure):
    """LBA format"""
    _pack_ = 1
    _fields_ = [
        ('GBL', c_uint8),   # 0 Group bit length
        ('PBL', c_uint8),   # PU bit length
        ('CBL', c_uint8),   # Chunk bit length
        ('BBL', c_uint8),   # Logical block bit length
        ('RSV0', c_uint32),
    ]


class Geometry(Structure):
    """Device Geometry Data Structure"""
    _pack_ = 1
    _fields_ = [
        ('MJR', c_uint8),           # Major Version Number
        ('MNR', c_uint8),           # Minor Version Number
        ('RSV0', c_uint8 * 6),      # Number of configuration groups
        ('LBAF', LBAF),             # LBA Format
        ('MCCAP', c_uint32),        # Media and Controller Capabilities
        ('RSV1', c_uint8 * 12),     # Current device operating mode
        ('WIT', c_uint8),           # Wear-level Index Delta Threshold
        ('RSV2', c_uint8 * 31),
        ('NUM_GRP', c_uint16),      # Number of Groups
        ('NUM_PU', c_uint16),       # Number of parallel units per group
        ('NUM_CHK', c_uint32),      # Number of chunks per parallel unit
        ('CLBA', c_uint32),         # Chunk Size
        ('RSV3', c_uint8 * 52),     # Description of the 4th group
        ('WS_MIN', c_uint32),       # Minimum Write Size
        ('WS_OPT', c_uint32),       # Optimal Write Size
        ('MW_CUNITS', c_uint32),    # Cache Minimum Write Size Units
        ('MAXOC', c_uint32),        # Maximum Open Chunks
        ('MAXOCPU', c_uint32),      # Maximum Open Chunks per PU
        ('RSV4', c_uint8 * 44),
        ('TRDT', c_uint32),         # tRD Typical
        ('TRDM', c_uint32),         # tRD Max
        ('TWRT', c_uint32),         # tWR Typical
        ('TWRM', c_uint32),         # tWR Max
        ('TCRST', c_uint32),        # tCRS Typical
        ('TCRSM', c_uint32),        # tCRS Max
        ('RSV5', c_uint8 * 40),
        ('RSV6', c_uint8 * 2816),
        ('VS', c_uint8 * 1024),     # Vendor Specific
    ]
