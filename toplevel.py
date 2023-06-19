import remap
import os
import oword
import namedparams
import logging
import json
import sys
import importlib
import logging_constants
import metrology
from calibstate import CalibState, Stages
from cmmmanager import Cmm
import v2state

POCKETNC_VAR_DIR = os.environ.get('POCKETNC_VAR_DIRECTORY')
logging.basicConfig(filename=os.path.join(POCKETNC_VAR_DIR, "python.log"),
  filemode='a',
  level=logging.DEBUG if os.environ.get('DEV') == "true" else logging.INFO,
  format=logging_constants.FORMAT,
  datefmt=logging_constants.DATEFMT
)
logger = logging.getLogger(__name__)

logger.debug("in toplevel.py 32346666")

def __init__(self):
# handle any per-module initialisation tasks here
  remap.init_stdglue(self)
  logger.debug("interp __init__ %s, %s",self.task,os.getpid())

def __delete__(self):
# handle any per-module shutdown tasks here
  logger.debug("interp __delete__ %s, %s",self.task,os.getpid())

def write_feature_map(name):
  try:
    manager = metrology.FeatureManager.getInstance()
    featureMap = manager.getActiveFeatureMap()
    dataString = json.dumps(featureMap.features, cls=metrology.FeatureEncoder)
    with open(os.path.join(POCKETNC_VAR_DIR, name + ".json"), "w") as file:
      file.write(dataString)
  except:
    logger.debug("Error saving feature map %s", name, exc_info=True)

def read_feature_map(name):
  try:
    manager = metrology.FeatureManager.getInstance()
    featureMap = manager.getActiveFeatureMap()
    featureMap.clear()
    with open(os.path.join(POCKETNC_VAR_DIR,name + ".json"), "r") as file:
      dataString = file.read()
    data = metrology.convertJSONDataToFeatures(json.loads(dataString))
    for k in data:
      if isinstance(data[k], metrology.Feature):
        featureMap.setFeature(int(k), data[k])
  except:
    logger.debug("Error reading feature map %s", name, exc_info=True)

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
