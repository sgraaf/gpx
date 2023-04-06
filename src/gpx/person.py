"""This module provides a Person object to contain a person or organization."""
from __future__ import annotations

from lxml import etree

from .element import Element
from .email import Email
from .link import Link
from .mixins import AttributesMutableMappingMixin


class Person(Element, AttributesMutableMappingMixin):
    """A person class for the GPX data format.

    A person or organization.

    Args:
        element: The person XML element. Defaults to `None`.
    """

    #: Name of person or organization.
    name: str | None = None

    #: Email address.
    email: Email | None = None

    #: Link to Web site or other external information about person.
    link: Link | None = None

    __keys__ = ("name", "email", "link")

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # name
        if (name := self._element.find("name", namespaces=self._nsmap)) is not None:
            self.name = name.text

        # email
        if (email := self._element.find("email", namespaces=self._nsmap)) is not None:
            self.email = Email(email)

        # link
        if (link := self._element.find("link", namespaces=self._nsmap)) is not None:
            self.link = Link(link)

    def _build(self, tag: str = "person") -> etree._Element:
        person = super()._build(tag)

        if self.name is not None:
            name = etree.SubElement(person, "name", nsmap=self._nsmap)
            name.text = self.name

        if self.email is not None:
            person.append(self.email._build())

        if self.link is not None:
            person.append(self.link._build())

        return person
