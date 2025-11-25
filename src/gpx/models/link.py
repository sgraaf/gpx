"""Link model for GPX data.

This module provides the Link model representing a link to an external resource
(Web page, digital photo, video clip, etc) with additional information, following
the GPX 1.1 specification.
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
class Link:
    """A link to an external resource with additional information.

    Args:
        href: URL of hyperlink.
        text: Text of hyperlink. Defaults to None.
        type: Mime type of content (e.g. image/jpeg). Defaults to None.

    """

    href: str
    text: str | None = None
    type: str | None = None

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse a Link from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed Link instance.

        Raises:
            ValueError: If required attributes are missing.

        """
        href_value = element.get("href")

        if href_value is None:
            msg = "Link element missing required 'href' attribute"
            raise ValueError(msg)

        # Parse optional text element
        text_value = None
        text_element = element.find("text")
        if text_element is not None:
            text_value = text_element.text

        # Parse optional type element
        type_value = None
        type_element = element.find("type")
        if type_element is not None:
            type_value = type_element.text

        return cls(href=href_value, text=text_value, type=type_value)

    def to_xml(
        self, tag: str = "link", nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the Link to an XML element.

        Args:
            tag: The XML tag name. Defaults to "link".
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        element.set("href", self.href)

        if self.text is not None:
            text_element = etree.SubElement(element, "text", nsmap=nsmap)
            text_element.text = self.text

        if self.type is not None:
            type_element = etree.SubElement(element, "type", nsmap=nsmap)
            type_element.text = self.type

        return element
