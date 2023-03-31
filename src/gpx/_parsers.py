"""This private module provides a collection of helper functions to parse XML data."""
from typing import Dict, List, Optional

from lxml import etree


def parse_links(
    el: etree._Element, nsmap: Optional[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """Parse an element for links."""
    links = []
    for _link in el.iterfind("link", namespaces=nsmap):
        link = {"href": _link.get("href")}
        if (text := _link.find("text", namespaces=nsmap)) is not None:
            link["text"] = text.text
        if (_type := _link.find("type", namespaces=nsmap)) is not None:
            link["type"] = _type.text
        links.append(link)
    return links
