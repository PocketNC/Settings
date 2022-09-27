print("in toplevel.py 4")

from importlib import reload

import remap
import os
import oword
import namedparams
import probe
import metrology
sys.path.append("/opt/calib/ippclient")
import ipp_tests
sys.path.append("/opt/calib/cmmcalib")
import calib

reload(oword)
reload(metrology)
reload(probe)
reload(namedparams)
reload(ipp_tests)
reload(calib)

def __init__(self):
# handle any per-module initialisation tasks here
  remap.init_stdglue(self)
  print("interp __init__",self.task,os.getpid())

def __delete__(self):
# handle any per-module shutdown tasks here
  print("interp __delete__",self.task,os.getpid())
