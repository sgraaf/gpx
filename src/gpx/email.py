"""This module provides a Email object to contain an email address."""
from __future__ import annotations

from lxml import etree

from .element import Element


class Email(Element):
    """An email class for the GPX data format.

    An email address. Broken into two parts (id and domain) to help prevent
    email harvesting.

    Args:
        element: The email XML element. Defaults to `None`.
    """

    #: id half of email address (e.g. billgates2004)
    id: str

    #: domain half of email address (e.g. hotmail.com)
    domain: str

    def _parse(self) -> None:
        super()._parse()

        # assertion to satisfy mypy
        assert self._element is not None

        # required
        self.id = self._element.get("id")
        self.domain = self._element.get("domain")

    def _build(self, tag: str = "email") -> etree._Element:
        email = super()._build(tag)
        email.set("id", self.id)
        email.set("domain", self.domain)

        return email

    def __str__(self) -> str:
        return f"{self.id}@{self.domain}"
