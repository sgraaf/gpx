"""Metadata model for GPX data.

This module provides the Metadata model containing information about the GPX
file, author, and copyright restrictions, following the GPX 1.1 specification.
"""

from __future__ import annotations

import datetime as dt  # noqa: TC003
from dataclasses import dataclass, field

from .base import GPXModel
from .bounds import Bounds  # noqa: TC001
from .copyright import Copyright  # noqa: TC001
from .link import Link  # noqa: TC001
from .person import Person  # noqa: TC001


@dataclass(kw_only=True, slots=True)
class Metadata(GPXModel):
    """Information about the GPX file, author, and copyright restrictions.

    Providing rich, meaningful information about your GPX files allows others
    to search for and use your GPS data.

    Args:
        name: The name of the GPX file. Defaults to None.
        desc: A description of the contents of the GPX file. Defaults to None.
        author: The person or organization who created the GPX file.
            Defaults to None.
        copyright: Copyright and license information governing use of the file.
            Defaults to None.
        link: URLs associated with the location described in the file.
            Defaults to empty list.
        time: The creation date of the file. Defaults to None.
        keywords: Keywords associated with the file. Search engines or
            databases can use this information to classify the data.
            Defaults to None.
        bounds: Minimum and maximum coordinates which describe the extent
            of the coordinates in the file. Defaults to None.

    """

    _tag = "metadata"

    name: str | None = None
    desc: str | None = None
    author: Person | None = None
    copyright: Copyright | None = None
    link: list[Link] = field(default_factory=list)
    time: dt.datetime | None = None
    keywords: str | None = None
    bounds: Bounds | None = None
