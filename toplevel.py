import remap
import os
import oword
import namedparams
import logging
import sys
import importlib
import logging_constants

POCKETNC_VAR_DIR = os.environ.get('POCKETNC_VAR_DIRECTORY')
logging.basicConfig(filename=os.path.join(POCKETNC_VAR_DIR, "python.log"),
  filemode='a',
  level=logging.DEBUG,
  format=logging_constants.FORMAT,
  datefmt=logging_constants.DATEFMT
)
logger = logging.getLogger(__name__)

logger.debug("in toplevel.py 48")

def __init__(self):
# handle any per-module initialisation tasks here
  remap.init_stdglue(self)
  logger.debug("interp __init__ %s, %s",self.task,os.getpid())

def __delete__(self):
# handle any per-module shutdown tasks here
  logger.debug("interp __delete__ %s, %s",self.task,os.getpid())


def reload_python():
  logger.debug("in reload_python");
  for (k,v) in list(sys.modules.items()):
    if k.startswith('__main__'):
      logger.debug("starts with __main__, skipping... %s" % k)
      continue

    try:
      if(v.__file__.startswith('/opt/cmm-calib') or
         v.__file__.startswith('/opt/ippclient') or
         v.__file__.startswith('/opt/pocketnc')):
        try:
          logger.debug("reloading... %s" % k)
          importlib.reload(v)
        except NotImplementedError:
          pass
        except:
          logger.debug("Error reloading module (%s,%s)", k, v, exc_info=True)
    except:
      pass

if os.environ.get('DEV') == "true":
  reload_python();
  reload_python(); #Call second time so all references are reloaded
  #For example oword might be reloaded before oword.v2_calib
  #The second reload will bring in the new references to oword.v2_calib
