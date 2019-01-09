#!/usr/bin/python 

from copy import deepcopy
import os
import re
import pprint
import sys
from version import getVersion

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
VERSION = getVersion()

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, merge_ini_data, write_ini_data

INI_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini")
INI_DEFAULT_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/versions/%s/PocketNC.ini" % VERSION)
CALIBRATION_OVERLAY_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/CalibrationOverlay.inc")
FEATURES_DIR = os.path.join(POCKETNC_DIRECTORY, "Settings/features")

if __name__ == "__main__":
  defaults = read_ini_data(INI_DEFAULT_FILE)

  if os.path.isfile(CALIBRATION_OVERLAY_FILE):
    overlay = read_ini_data(CALIBRATION_OVERLAY_FILE)
  else:
    overlay = { 'parameters': [],
                'sections': {} }

  merged = merge_ini_data(defaults, overlay)

  for param in overlay['parameters']:
    section = param['values']['section']
    name = param['values']['name']
    value = param['values']['value']

    if section == "POCKETNC_FEATURES":
      dir = os.path.join(FEATURES_DIR, name.lower())

      feature_overlay_path = os.path.join(dir, "overlay.inc")

      if os.path.isfile(feature_overlay_path):
          feature_overlay = read_ini_data(feature_overlay_path)
          merged = merge_ini_data(merged, feature_overlay)
    

  write_ini_data(merged, INI_FILE);
