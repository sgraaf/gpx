"""Copyright model for GPX data.

This module provides the Copyright model containing information about the
copyright holder and any license governing use of the GPX data, following the
GPX 1.1 specification.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import GPXModel


@dataclass(frozen=True)
class Copyright(GPXModel):
    """Information about the copyright holder and any license.

    By linking to an appropriate license, you may place your data into the
    public domain or grant additional usage rights.

    Args:
        author: Copyright holder (e.g. TopoSoft, Inc.)
        year: Year of copyright. Defaults to None.
        license: Link to external file containing license text. Defaults to None.

    """

    _tag = "copyright"

    author: str
    year: int | None = None
    license: str | None = None
