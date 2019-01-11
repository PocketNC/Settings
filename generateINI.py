#!/usr/bin/python 

from copy import deepcopy
import os
import re
import pprint
import sys
from version import getVersion
import subprocess

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
VERSION = getVersion()

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, merge_ini_data, write_ini_data, append_ini_data

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

  features = set()

  # Auto detected features
  for feature in os.listdir(FEATURES_DIR):
    feature_path = os.path.join(FEATURES_DIR, feature)
    detect_path = os.path.join(feature_path, "detect")

    if os.path.isfile(detect_path):
      detected = subprocess.check_output(detect_path).strip()
      if detected == "1":
        print "Detected feature, %s" % feature
        features.add(feature)

  # Manually enabled/disabled features
  for param in overlay['parameters']:
    section = param['values']['section']
    name = param['values']['name']
    value = param['values']['value']

    if section == "POCKETNC_FEATURES":
      feature = name.lower()
      if value == "1":
        features.add(feature)
      elif value == "0" and feature in features:
        features.remove(feature)
        

  for feature in features:
    dir = os.path.join(FEATURES_DIR, feature)

    feature_overlay_path = os.path.join(dir, "overlay.inc")
    feature_append_path = os.path.join(dir, "append.inc")
    feature_startup_path = os.path.join(dir, "startup")

    if os.path.isfile(feature_overlay_path):
      feature_overlay = read_ini_data(feature_overlay_path)
      merged = merge_ini_data(merged, feature_overlay)

    if os.path.isfile(feature_append_path):
      feature_append = read_ini_data(feature_append_path)
      merged = append_ini_data(merged, feature_append)

    if os.path.isfile(feature_startup_path):
      subprocess.check_output(feature_startup_path);

  write_ini_data(merged, INI_FILE);
