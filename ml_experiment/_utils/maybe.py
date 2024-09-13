from __future__ import annotations
from typing import Callable, Generic, TypeVar


T = TypeVar('T')
U = TypeVar('U')

class Maybe(Generic[T]):
    def __init__(self, v: T | None):
        self._v: T | None = v


    def map(self, f: Callable[[T], U | None]) -> Maybe[U]:
        if self._v is None:
            return Maybe[U](None)

        u = f(self._v)
        return Maybe(u)


    def flat_map(self, f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        if self._v is None:
            return Maybe[U](None)

        return f(self._v)


    def flat_otherwise(self, f: Callable[[], Maybe[T]]) -> Maybe[T]:
        if self._v is None:
            return f()

        return self


    def or_else(self, t: T) -> T:
        if self._v is None:
            return t

        return self._v


    def expect(self, msg: str = '') -> T:
        if self._v is None:
            raise Exception(msg)

        return self._v


    def is_none(self):
        return self._v is None


    def is_some(self):
        return self._v is not None
