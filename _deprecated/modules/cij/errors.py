"""
Errors that are used across cijoe modules.

NOTE: new errors should inherit from CIJError. This allows users to catch all
cijoe-related errors using a single type.
"""


class CIJError(Exception):
    """Wrapper for all CIJOE errors"""


class InitializationError(CIJError):
    """Raised when failing to initialize data structures"""


class InvalidRangeError(CIJError):
    """Raised for range formatting errors"""


class UnknownUnitError(CIJError):
    """Raised when attempting to use unknown units"""
