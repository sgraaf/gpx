"""GPX dataclass-based models.

This package provides dataclass-based models for GPX elements following the
GPX 1.1 specification as closely as possible.
"""

from __future__ import annotations

from .bounds import Bounds
from .copyright import Copyright
from .email import Email
from .link import Link

__all__ = [
    "Bounds",
    "Copyright",
    "Email",
    "Link",
]
