"""Base class for GPX dataclass models.

This module provides the base class that all GPX dataclass models inherit from,
implementing common XML parsing and serialization logic.
"""

from __future__ import annotations

from typing import ClassVar, Self

from lxml import etree

from .utils import build_to_xml, parse_from_xml

#: GPX 1.1 namespace
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"


class GPXModel:
    """Base class for GPX dataclass models.

    Provides common XML parsing and serialization methods. Subclasses must
    define the `_tag` class attribute to specify the default XML tag name.

    Attributes:
        _tag: The default XML tag name for this model.

    """

    _tag: ClassVar[str]

    @classmethod
    def from_xml(cls, element: etree._Element) -> Self:
        """Parse the model from an XML element.

        Args:
            element: The XML element to parse.

        Returns:
            The parsed model instance.

        Raises:
            ValueError: If required attributes are missing.

        """
        return cls(**parse_from_xml(cls, element))

    def to_xml(
        self, tag: str | None = None, nsmap: dict[str | None, str] | None = None
    ) -> etree._Element:
        """Convert the model to an XML element.

        Args:
            tag: The XML tag name. Defaults to the model's `_tag` attribute.
            nsmap: Optional namespace mapping. Defaults to GPX 1.1 namespace.

        Returns:
            The XML element.

        """
        if tag is None:
            tag = self._tag

        if nsmap is None:
            nsmap = {None: GPX_NAMESPACE}

        element = etree.Element(tag, nsmap=nsmap)
        build_to_xml(self, element, nsmap=nsmap)

        return element
