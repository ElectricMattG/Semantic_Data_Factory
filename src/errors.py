"""
Custom error definitions.
"""


class UnresolvedTransientError(Exception):
    """
    Raised when transient errors can't be resolved.
    """

    pass


class InvalidJSONError(Exception):
    """
    Raised when JSON isn't valid.
    """

    pass


class InvalidConfig(Exception):
    """
    Raised when config is invalid
    """

    pass