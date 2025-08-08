from typing import Callable, Iterable, Any
from collections import OrderedDict
from abc import ABC, abstractmethod

class BaseLazyList(ABC):
    def __init__(self, length: int, max_cache_size=128):
        self._length = length
        self._max_cache_size = max_cache_size
        self._cache = OrderedDict()

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        if not (0 <= index < self._length):
            raise IndexError("Index out of range")

        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]

        value = self.load_item(index)
        self._cache[index] = value
        self._cache.move_to_end(index)

        if len(self._cache) > self._max_cache_size:
            old_index, old_value = self._cache.popitem(last=False)
            self.on_evict_index(old_index, old_value)

        return value

    @abstractmethod
    def load_item(self, index):
        pass

    def on_evict(self, value):
        """Be called when the value in list is deprecated."""
        pass

    def on_evict_index(self, index, value):
        return self.on_evict(value)

    def cache_clear(self):
        """Use on_evict() on each value."""
        while self._cache:
            index, value = self._cache.popitem(last=False)
            self.on_evict_index(index, value)

    def __iter__(self):
        for i in range(self._length):
            yield self[i]


class LazyList(BaseLazyList):
    def __init__(self, iterable: Iterable, func=id, max_cache_size=128, on_evict=id):
        self._func = func
        self._data = list(iterable)
        self._on_evict = on_evict
        super().__init__(len(self._data), max_cache_size)

    def load_item(self, index):
        return self._func(self._data[index])

    def on_evict(self, value):
        return self._on_evict(value)

    def __repr__(self):
        if len(self) == 0:
            return f"<LazyList object at {hex(id(self))} of length: 0>"
        return f"<LazyList object at {hex(id(self))} of length: {len(self)}, index type: {type(self._data[0])}>"

    def __str__(self):
        if len(self) == 0:
            return f"<LazyList object at {hex(id(self))} of length: 0>"
        return f"<LazyList object at {hex(id(self))} of length: {len(self)}, data type: {type(self._data[0])} -> {type(self[0])}>"


def map_lazylist(func: Callable[[Any], Any], iterable: Iterable[Any], max_cache_size=128, on_evict: Callable[[Any], Any] =lambda v: None):
    """Like map(), but return LazyList object which support LRU cache and random access."""
    ls = LazyList(iterable, func, max_cache_size, on_evict)
    return ls
