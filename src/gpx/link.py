"""
This module provides a Link object to contain GPX links to external resources
(Web page, digital photo, video clip, etc) with additional information.
"""
from __future__ import annotations

from lxml import etree

from .element import Element


class Link(Element):
    """A link class for the GPX data format.

    A link to an external resource (Web page, digital photo, video clip, etc)
    with additional information.

    Args:
        element: The link XML element. Defaults to `None`.
    """

    #: URL of hyperlink.
    href: str

    #: Text of hyperlink.
    text: str | None = None

    #: Mime type of content (e.g. image/jpeg)
    type: str | None = None

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # required
        self.href = self._element.get("href")

        # text
        if (text := self._element.find("text", namespaces=self._nsmap)) is not None:
            self.text = text.text

        # type
        if (_type := self._element.find("type", namespaces=self._nsmap)) is not None:
            self.type = _type.text

    def _build(self, tag: str = "link") -> etree._Element:
        link = super()._build(tag)
        link.set("href", self.href)

        if self.text is not None:
            text = etree.SubElement(link, "text", nsmap=self._nsmap)
            text.text = self.text

        if self.type is not None:
            _type = etree.SubElement(link, "type", nsmap=self._nsmap)
            _type.text = self.type

        return link
