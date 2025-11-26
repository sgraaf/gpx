"""Link model for GPX data.

This module provides the Link model representing a link to an external resource
(Web page, digital photo, video clip, etc) with additional information, following
the GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import GPXModel


@dataclass(frozen=True)
class Link(GPXModel):
    """A link to an external resource with additional information.

    Args:
        href: URL of hyperlink.
        text: Text of hyperlink. Defaults to None.
        type: Mime type of content (e.g. image/jpeg). Defaults to None.

    """

    _tag = "link"

    href: str
    text: str | None = None
    type: str | None = None
