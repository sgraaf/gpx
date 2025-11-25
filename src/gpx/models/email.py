"""Email model for GPX data.

This module provides the Email model representing an email address broken into
two parts (id and domain) to help prevent email harvesting, following the GPX
1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from lxml import etree

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


@dataclass(frozen=True)
class Email:
    """An email address.

    Broken into two parts (id and domain) to help prevent email harvesting.

    Args:
        id: id half of email address (e.g. billgates2004)
        domain: domain half of email address (e.g. hotmail.com)

    """

    id: str
    domain: str

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse an Email from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Email instance.

        Raises:
            ValueError: If required attributes are missing.

        """
        id_value = element.get("id")
        domain_value = element.get("domain")

        if id_value is None:
            msg = "Email element missing required 'id' attribute"
            raise ValueError(msg)

        if domain_value is None:
            msg = "Email element missing required 'domain' attribute"
            raise ValueError(msg)

        return cls(id=id_value, domain=domain_value)

    def to_xml(
        self, tag: str = "email", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Email to an XML element.

        Args:
            tag: The XML tag name. Defaults to "email".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        element.set("id", self.id)
        element.set("domain", self.domain)

        return element

    def __str__(self) -> str:
        """Return the email address as a string.

        Returns:
            The email address in standard format (id@domain).

        """
        return f"{self.id}@{self.domain}"
