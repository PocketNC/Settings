"""
Python functions that can be called from a G code context using #<_function_name> syntax. See
[LinuxCNC](http://linuxcnc.org/docs/2.8/html/remap/remap.html#remap:adding-predefined-named-parameters) documentation for more info.
"""
import math
import sys
import inspect

from .probe import *
from .penta import *
from .v2_calib import *

from oword import return_exception_as_string, await_return_exception_as_string

# These wrap all functions and coroutines with decorators. The coroutines will
# properly await until they're done running. Both will catch any exceptions and
# return a string representing the exception, so the interpreter will show the
# string as an error and abort. This is also done in oword.
module = sys.modules[__name__]
for (name, f) in inspect.getmembers(module, inspect.iscoroutinefunction):
  setattr(module, name, await_return_exception_as_string(f))

for (name, f) in inspect.getmembers(module, inspect.isfunction):
  if name not in [ "return_exception_as_string", "await_return_exception_as_string" ]:
    setattr(module, name, return_exception_as_string(f))
