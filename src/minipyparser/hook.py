from typing import TypeVar, Generic

from io import TextIOBase

class BaseHook:
    def __init__(self, source, index=0):
        self.source = source
        self.index = index
        self.cache = list()
    
    def __repr__(self):
        return f'{type(self).__name__}({self.source}, {self.cache}, {self.index})'
    
    def __iter__(self):
        while cached := self.take():
            yield cached
        
        return
    
    def take(self, _count=1):
        raise NotImplementedError
    
    def test(self, *values: str) -> str | None:
        index = self.index

        for value in values:
            if value == self.take(len(value)):
                return value

            self.index = index
        
        return
    
    def drop(self, by=1) -> int:
        self.index -= by

        if self.index < 0:
            raise IndexError('hook index should be greater than zero')
        
        return self.index

class TextHook(BaseHook):
    def take(self, count=1) -> str:
        if count > 1:
            return "".join(self.take() for _ in range(count))

        if self.index < len(self.cache):
            cached = self.cache[self.index]
        else:
            cached = self.source.read(1)
            self.cache.append(cached)

        self.index += 1
        
        return cached