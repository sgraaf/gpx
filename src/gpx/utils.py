"""This module contains various utility functions."""
import re


def remove_encoding_from_string(s: str) -> str:
    """
    Removes encoding declarations (e.g. encoding="utf-8") from the string, if
    any.

    Args:
        s: The string.

    Returns:
        The string with any encoding declarations removed.
    """
    return re.sub(r"(encoding=[\"\'].+[\"\'])", "", s)
