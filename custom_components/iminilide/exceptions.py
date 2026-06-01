class IminilideError(Exception):
    """Base error for the i-MINILide integration."""


class IminilideConnectionError(IminilideError):
    """Raised when the controller cannot be reached."""


class IminilideParseError(IminilideError):
    """Raised when the controller response cannot be parsed."""
