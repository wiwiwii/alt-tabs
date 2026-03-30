class AltTabsError(Exception):
    """Base class for predictable domain failures."""


class RangeNotPlayableError(AltTabsError):
    """Raised when requested transposition/retab target cannot be played."""


class InvalidAnchorError(AltTabsError):
    """Raised when target anchor string/fret is invalid for instrument."""


class PolyphonyNotSupportedError(AltTabsError):
    """Raised when a monophonic stage receives polyphonic input."""
