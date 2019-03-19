#!/usr/bin/env python
"""
identify.py     - NVMe Identify
"""
from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_uint64
# pylint: disable=locally-disabled, too-few-public-methods


class IdentifyCDS(Structure):
    """Identify - Identify Controller Data Structure"""
    _pack_ = 1
    _fields_ = [
        ('VID', c_uint16),          # PCI Vendor ID
        ('SSVID', c_uint16),        # PCI Subsystem Vendor ID
        ('SN', c_uint8 * 20),       # Serial Number
        ('MN', c_uint8 * 40),       # Model Number
        ('FR', c_uint64),           # Firmware Revision
        ('RAB', c_uint8),           # Recommended Arbitration Burst
        ('IEEE', c_uint32, 24),     # IEEE OUI Identifier
        ('CMIC', c_uint32, 8),      # Controller Multi-Path I/O and Namespace Sharing Capabilities
        ('MDTS', c_uint8),          # Maximum Data Transfer Size
        ('CNTLID', c_uint16),       # Controller ID
        ('VER', c_uint32),          # Version
        ('RTD3R', c_uint32),        # RTD3 Resume Latency
        ('RTD3E', c_uint32),        # RTD3 Entry Latency
        ('OAES', c_uint32),         # Optional Asynchronous Events Supported
        ('RSV0', c_uint8 * 144),
        ('NMIS', c_uint8 * 16),     # Refer to the NVMe Management Interface Specification
        ('OACS', c_uint16),         # Optional Admin Command Support
        ('ACL', c_uint8),           # Abort Command Limit
        ('AERL', c_uint8),          # Asynchronous Event Request Limit
        ('FRMW', c_uint8),          # Firmware Updates
        ('LPA', c_uint8),           # Log Page Attributes
        ('ELPE', c_uint8),          # Error Log Page Entries
        ('NPSS', c_uint8),          # Number of Power States Support
        ('AVSCC', c_uint8),         # Admin Vendor Specific Command Configuration
        ('APSTA', c_uint8),         # Autonomous Power State Transition Attributes
        ('WCTEMP', c_uint16),       # Warning Composite Temperature Threshold
        ('CCTEMP', c_uint16),       # Critical Composite Temperature Threshold
        ('MTFA', c_uint16),         # Maximum Time for Firmware Activation
        ('HMPRE', c_uint32),        # Host Memory Buffer Preferred Size
        ('HMMIN', c_uint32),        # Host Memory Buffer Minimum Size
        ('TNVMCAP', c_uint8 * 16),  # Total NVM Capacity
        ('UNVMCAP', c_uint8 * 16),  # Unallocated NVM Capacity
        ('RPMBS', c_uint32),        # Replay Protected Memory Block Support
        ('RSV1', c_uint8 * 196),
        ('SQES', c_uint8),          # Submission Queue Entry Size
        ('CQES', c_uint8),          # Completion Queue Entry Size
        ('RSV2', c_uint8 * 2),
        ('NN', c_uint32),           # Number of Namespaces
        ('ONCS', c_uint16),         # Optional NVM Command Support
        ('FUSES', c_uint16),        # Fused Operation Support
        ('FNA', c_uint8),           # Format NVM Attributes
        ('VWC', c_uint8),           # Volatile Write Cache
        ('AWUN', c_uint16),         # Atomic Write Unit Normal
        ('AWUPF', c_uint16),        # Atomic Write Unit Power Fail
        ('NVSCC', c_uint8),         # NVM Vendor Specific Command Configuration
        ('RSV3', c_uint8),
        ('ACWU', c_uint16),         # Atomic Compare & Write Unit
        ('RSV4', c_uint8 * 2),
        ('SGLS', c_uint32),         # SGL Support
        ('RSV5', c_uint8 * 164),
        ('RSV6', c_uint8 * 1344),
        ('PSD0', c_uint8 * 32),     # Power State 0 Descriptor
        ('PSD1', c_uint8 * 32),     # Power State 1 Descriptor
        ('PSD2', c_uint8 * 32),     # Power State 2 Descriptor
        ('PSD3', c_uint8 * 32),     # Power State 3 Descriptor
        ('PSD4', c_uint8 * 32),     # Power State 4 Descriptor
        ('PSD5', c_uint8 * 32),     # Power State 5 Descriptor
        ('PSD6', c_uint8 * 32),     # Power State 6 Descriptor
        ('PSD7', c_uint8 * 32),     # Power State 7 Descriptor
        ('PSD8', c_uint8 * 32),     # Power State 8 Descriptor
        ('PSD9', c_uint8 * 32),     # Power State 9 Descriptor
        ('PSD10', c_uint8 * 32),    # Power State 10 Descriptor
        ('PSD11', c_uint8 * 32),    # Power State 11 Descriptor
        ('PSD12', c_uint8 * 32),    # Power State 12 Descriptor
        ('PSD13', c_uint8 * 32),    # Power State 13 Descriptor
        ('PSD14', c_uint8 * 32),    # Power State 14 Descriptor
        ('PSD15', c_uint8 * 32),    # Power State 15 Descriptor
        ('PSD16', c_uint8 * 32),    # Power State 16 Descriptor
        ('PSD17', c_uint8 * 32),    # Power State 17 Descriptor
        ('PSD18', c_uint8 * 32),    # Power State 18 Descriptor
        ('PSD19', c_uint8 * 32),    # Power State 19 Descriptor
        ('PSD20', c_uint8 * 32),    # Power State 20 Descriptor
        ('PSD21', c_uint8 * 32),    # Power State 21 Descriptor
        ('PSD22', c_uint8 * 32),    # Power State 22 Descriptor
        ('PSD23', c_uint8 * 32),    # Power State 23 Descriptor
        ('PSD24', c_uint8 * 32),    # Power State 24 Descriptor
        ('PSD25', c_uint8 * 32),    # Power State 25 Descriptor
        ('PSD26', c_uint8 * 32),    # Power State 26 Descriptor
        ('PSD27', c_uint8 * 32),    # Power State 27 Descriptor
        ('PSD28', c_uint8 * 32),    # Power State 28 Descriptor
        ('PSD29', c_uint8 * 32),    # Power State 29 Descriptor
        ('PSD30', c_uint8 * 32),    # Power State 30 Descriptor
        ('PSD31', c_uint8 * 32),    # Power State 31 Descriptor
        ('VS', c_uint8 * 1024),     # Vendor Specific
    ]


class IdentifyPSDDS(Structure):
    """Identify - Power State Descriptor Data Structure"""
    _pack_ = 1
    _fields_ = [
        ('MP', c_uint16),           # Active Power Scale
        ('RSV0', c_uint8),
        ('MPS', c_uint8, 1),        # Max Power Scale
        ('NOPS', c_uint8, 1),       # Non-Operational State
        ('RSV1', c_uint8, 6),
        ('ENLAT', c_uint32),        # Entry Latency
        ('EXLAT', c_uint32),        # Exit Latency
        ('RRT', c_uint8, 5),        # Relative Read Throughput
        ('RSV2', c_uint8, 3),
        ('RRL', c_uint8, 5),        # Relative Read Latency
        ('RSV3', c_uint8, 3),
        ('RWT', c_uint8, 5),        # Relative Write Throughput
        ('RSV4', c_uint8, 3),
        ('RWL', c_uint8, 5),        # Relative Write Latency
        ('RSV5', c_uint8, 3),
        ('IDLP', c_uint16),         # Idle Power
        ('RSV6', c_uint8, 6),
        ('IPS', c_uint8, 2),        # Idle Power Scale
        ('RSV7', c_uint8),
        ('ACTP', c_uint16),         # Active Power
        ('APW', c_uint8, 3),        # Active Power Workload
        ('RSV8', c_uint8, 3),
        ('APS', c_uint8, 2),        # Active Power Scale
        ('RSV9', c_uint8 * 9),
    ]


class IdentifyLbaf(Structure):
    """Identify - LBA Format Data Structure, NVM Command Set Specific"""
    _pack_ = 1
    _fields_ = [
        ('MS', c_uint16),       # Metadata Size
        ('LBADS', c_uint8),     # LBA Data Size
        ('RP', c_uint8, 2),     # Relative Performance
        ('RSV', c_uint8, 6),
    ]


class IdentifyNDS(Structure):
    """Identify - Identify Namespace Data Structure, NVM Command Set Specific"""
    _pack_ = 1
    _fields_ = [
        ('NSZE', c_uint64),         # Namespace Size
        ('NCAP', c_uint64),         # Namespace Capacity
        ('NUSE', c_uint64),         # Namespace Utilization
        ('NSFEAT', c_uint8),        # Namespace Features
        ('NLBAF', c_uint8),         # Number of LBA Formats
        ('FLBAS', c_uint8),         # Formatted LBA Size
        ('MC', c_uint8),            # Metadata Capabilities
        ('DPC', c_uint8),           # End-to-end Data Protection Capabilities
        ('DPS', c_uint8),           # End-to-end Data Protection Type Settings
        ('NMIC', c_uint8),          # Namespace Multi-path I/O and Namespace Sharing Capabilities
        ('RESCAP', c_uint8),        # Reservation Capabilities
        ('FPI', c_uint8),           # Format Progress Indicator
        ('RSV0', c_uint8),
        ('NAWUN', c_uint16),        # Namespace Atomic Write Unit Normal
        ('NAWUPF', c_uint16),       # Namespace Atomic Write Unit Power Fail
        ('NACWU', c_uint16),        # Namespace Atomic Compare & Write Unit
        ('NABSN', c_uint16),        # Namespace Atomic Boundary Size Normal
        ('NABO', c_uint16),         # Namespace Atomic Boundary Offset
        ('NABSPF', c_uint16),       # Namespace Atomic Boundary Size Power Fail
        ('RSV1', c_uint8 * 2),
        ('NVMECAP', c_uint8 * 16),  # NVM Capacity
        ('RSV2', c_uint8 * 40),
        ('NGUID', c_uint8 * 16),    # Namespace Globally Unique Identifier
        ('EUI64', c_uint64),        # IEEE Extended Unique Identifier
        ('LBAF', IdentifyLbaf * 16),        # LBA Format Support
        ('RSV3', c_uint8 * 192),
        ('VS', c_uint8 * 3712),     # Vendor Specific
    ]


class IdentifyLFDS(Structure):
    """Identify - LBA Format Data Structure, NVM Command Set Specific"""
    _pack_ = 1
    _fields_ = [
        ('MS', c_uint32, 16),       # Metadata Size
        ('LBADS', c_uint32, 8),     # LBA Data Size
        ('RP', c_uint32, 2),        # Relative Performance
        ('RSV', c_uint32, 6),
    ]
