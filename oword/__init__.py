"""
Python functions that can be called from a G code context using o<name_of_function> call syntax. See
[LinuxCNC](http://linuxcnc.org/docs/2.8/html/remap/remap.html) documentation for more info.
"""
import asyncio

import sys
import logging
import inspect

logger = logging.getLogger(__name__)
logger.debug("imported oword")

from .v2_calib import *
from .cmm import *
from .penta import *
from .probe import *

def do_nothing(self):
  logger.debug("in do_nothing")
  logger.debug("in do_nothing again")
  logger.debug("in do_nothing again2")
  pass

def do_error(self):
  logger.debug("in do_error")
  return "This is an error"

def return_int(self):
  logger.debug("in return_int")
  return 1

def return_exception_as_string(func):
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except Exception as e:
      msg = "%s: %s" % (type(e).__name__, str(e))
      logger.error(msg, exc_info=True)
      return msg
  return wrapper

def await_return_exception_as_string(func):
  def wrapper(*args, **kwargs):
    try:
      return asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))
    except Exception as e:
      msg = "%s: %s" % (type(e).__name__, str(e))
      logger.error(msg, exc_info=True)
      return msg
  return wrapper

# These wrap all functions and coroutines with decorators. The coroutines will
# properly await until they're done running. Both will catch any exceptions and
# return a string representing the exception, so the interpreter will show the
# string as an error and abort. This is also done in namedparams.
module = sys.modules[__name__]
for (name, f) in inspect.getmembers(module, inspect.iscoroutinefunction):
  setattr(module, name, await_return_exception_as_string(f))

for (name, f) in inspect.getmembers(module, inspect.isfunction):
  if name not in [ "return_exception_as_string", "await_return_exception_as_string" ]:
    setattr(module, name, return_exception_as_string(f))
