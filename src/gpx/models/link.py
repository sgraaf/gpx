"""Link model for GPX data.

This module provides the Link model representing a link to an external resource
(Web page, digital photo, video clip, etc) with additional information, following
the GPX 1.1 specification.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from lxml import etree

from .utils import (
    build_xml_attributes,
    build_xml_elements,
    parse_xml_attributes,
    parse_xml_elements,
)

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
        # Parse attributes
        kwargs = parse_xml_attributes(cls, element, attribute_names={"href"})
        # Parse child elements
        kwargs.update(parse_xml_elements(cls, element, element_names={"text", "type"}))
        return cls(**kwargs)

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
        build_xml_attributes(self, element, attribute_names={"href"})
        build_xml_elements(self, element, element_names={"text", "type"}, nsmap=nsmap)

        return element
