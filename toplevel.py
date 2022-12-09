from importlib import reload

import remap
import os
import oword
import namedparams
import probe
import metrology
import ipp_tests
import calib
import logging

POCKETNC_VAR_DIR = os.environ.get('POCKETNC_VAR_DIRECTORY')
logging.basicConfig(filename=os.path.join(POCKETNC_VAR_DIR, "python.log"),
  filemode='a',
  level=logging.DEBUG,
  format='%(asctime)s,%(msecs)d %(name)s %(levelname)s line %(lineno)d: %(message)s',
  datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

logger.debug("in toplevel.py 8")


reload(oword)
reload(metrology)
reload(probe)
reload(namedparams)
reload(ipp_tests)
reload(calib)

def __init__(self):
# handle any per-module initialisation tasks here
  remap.init_stdglue(self)
  logger.debug("interp __init__ %s, %s",self.task,os.getpid())

def __delete__(self):
# handle any per-module shutdown tasks here
  logger.debug("interp __delete__ %s, %s",self.task,os.getpid())
