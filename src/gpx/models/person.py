"""Person model for GPX data.

This module provides the Person model representing a person or organization,
following the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import GPXModel
from .email import Email  # noqa: TC001
from .link import Link  # noqa: TC001


@dataclass(frozen=True)
class Person(GPXModel):
    """A person or organization.

    Args:
        name: Name of person or organization. Defaults to None.
        email: Email address. Defaults to None.
        link: Link to Web site or other external information about person.
            Defaults to None.

    """

    _tag = "author"

    name: str | None = None
    email: Email | None = None
    link: Link | None = None
