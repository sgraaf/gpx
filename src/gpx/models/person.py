"""Person model for GPX data.

This module provides the Person model representing a person or organization,
following the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from lxml import etree

from .email import Email  # noqa: TC001
from .link import Link  # noqa: TC001
from .utils import build_to_xml, parse_from_xml

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Person:
    """A person or organization.

    Args:
        name: Name of person or organization. Defaults to None.
        email: Email address. Defaults to None.
        link: Link to Web site or other external information about person.
            Defaults to None.

    """

    name: str | None = None
    email: Email | None = None
    link: Link | None = None

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Person from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Person instance.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str = "author", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Person to an XML element.

        Args:
            tag: The XML tag name. Defaults to "author".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
