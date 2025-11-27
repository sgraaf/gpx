"""Email model for GPX data.

This module provides the Email model representing an email address broken into
two parts (id and domain) to help prevent email harvesting, following the GPX
1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import GPXModel


@dataclass(slots=True)
class Email(GPXModel):
    """An email address.

    Broken into two parts (id and domain) to help prevent email harvesting.

    Args:
        id: id half of email address (e.g. billgates2004)
        domain: domain half of email address (e.g. hotmail.com)

    """

    _tag = "email"

    id: str
    domain: str

    def __str__(self) -> str:
        """Return the email address as a string.

        Returns:
            The email address in standard format (id@domain).

        """
        return f"{self.id}@{self.domain}"
