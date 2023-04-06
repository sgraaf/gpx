"""This module provides a Person object to contain a person or organization."""
from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from typing import Any, Iterable, Iterator, overload

from .waypoint import Waypoint


class AttributesMutableMappingMixin(MutableMapping):
    """
    A mixin class to provide a `MutableMapping` interface to an object's defined
    attributes.
    """

    #: A tuple of attribute names that are to be treated as keys.
    __keys__: tuple[str, ...]

    def __getitem__(self, key: str) -> Any | None:
        if key not in self.__keys__:
            raise KeyError(f"Key not found: {key}")
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any | None) -> None:
        if key not in self.__keys__:
            raise KeyError(f"Key not found: {key}")
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        if key not in self.__keys__:
            raise KeyError(f"Key not found: {key}")
        setattr(self, key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__keys__)

    def __len__(self) -> int:
        return len(self.__keys__)


class PointsSequenceMixin(Sequence):
    """A mixin class to provide a `Sequence` interface to an object's points."""

    #: A list of points.
    points: list[Waypoint]

    @overload
    def __getitem__(self, index: int) -> Waypoint:
        ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Waypoint]:
        ...

    def __getitem__(self, index: int | slice) -> Waypoint | MutableSequence[Waypoint]:
        return self.points[index]

    def __iter__(self) -> Iterator[Waypoint]:
        yield from self.points

    def __len__(self) -> int:
        return len(self.points)


class PointsMutableSequenceMixin(PointsSequenceMixin, MutableSequence):
    """
    A mixin class to provide a `MutableSequence` interface to an object's
    points.
    """

    @overload
    def __setitem__(self, index: int, value: Waypoint) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Waypoint]) -> None:
        ...

    def __setitem__(
        self, index: int | slice, value: Waypoint | Iterable[Waypoint]
    ) -> None:
        if isinstance(index, int) and isinstance(value, Waypoint):
            self.points[index] = value
        if isinstance(index, slice) and isinstance(value, Iterable):
            self.points[index] = value
        raise TypeError("Invalid type of index or value.")

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index: int | slice) -> None:
        del self.points[index]

    def insert(self, index: int, value: Waypoint) -> None:
        self.points.insert(index, value)
