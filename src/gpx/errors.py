"""This module provices various error types."""


class InvalidGPXError(Exception):
    """GPX is invalid."""


class ParseError(Exception):
    """No element to parse."""
