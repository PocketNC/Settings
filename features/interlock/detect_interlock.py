#!/usr/bin/python
import os
import time

def detect():
  from cStringIO import StringIO
  import sys

  class Capturing(list):
    def __enter__(self):
      self._stdout = sys.stdout
      sys.stdout = self._stringio = StringIO()
      return self
    def __exit__(self, *args):
      self.extend(self._stringio.getvalue().splitlines())
      del self._stringio    # free up some memory
      sys.stdout = self._stdout 
  
  with Capturing() as output:
    try:
      return 1

if __name__ == '__main__':
  print detect()
