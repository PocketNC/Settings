from ctypes import *
from _typeshed import Incomplete

lib: Incomplete

class HalException(Exception): ...

class halType:
    BIT: int
    FLOAT: int
    SIGNED: int
    UNSIGNED: int
    PORT: int
    values: Incomplete
    typeConversion: Incomplete

class pinDir:
    IN: int
    OUT: int
    IO: Incomplete
    values: Incomplete

class pin:
    comp: Incomplete
    name: Incomplete
    type: Incomplete
    dir: Incomplete
    data_ptr: Incomplete
    def __init__(self, component, name, type, dir, data_ptr) -> None: ...
    @property
    def fullname(self): ...
    @property
    def value(self): ...

class port(pin):
    def __init__(self, component, name, type, dir, data_ptr) -> None: ...
    def read(self, count): ...
    def peek(self, count): ...
    def peek_commit(self, count): ...
    def write(self, buff): ...
    def readable(self): ...
    def writable(self): ...
    def size(self): ...
    def clear(self) -> None: ...
    def waitReadable(self, count) -> None: ...
    def waitWritable(self, count) -> None: ...

class component:
    id: Incomplete
    pins: Incomplete
    def __init__(self, name) -> None: ...
    def __del__(self) -> None: ...
    def exit(self) -> None: ...
    def ready(self) -> None: ...
    def name(self): ...
    def pinNew(self, name, type, dir): ...
    def sigNew(self, name, type) -> None: ...
    def sigLink(self, pin_name, sig_name) -> None: ...
    def halMalloc(self, count): ...
