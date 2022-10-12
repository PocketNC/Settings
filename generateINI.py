#!/usr/bin/python3

from copy import deepcopy
import os
import re
import pprint
import sys
from version import getVersion
import subprocess

POCKETNC_DIRECTORY = os.environ.get('POCKETNC_DIRECTORY')
POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
VERSION = getVersion()

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, merge_ini_data, write_ini_data, append_ini_data, rename_section
INI_DEFAULT_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/versions/%s/PocketNC.ini" % VERSION)

INI_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini")
CALIBRATION_OVERLAY_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "CalibrationOverlay.inc")
LAST_TOOL_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "LastTool.inc")
FEATURES_DIR = os.path.join(POCKETNC_DIRECTORY, "Settings/features")

if __name__ == "__main__":
  defaults = read_ini_data(INI_DEFAULT_FILE)

  if os.path.isfile(CALIBRATION_OVERLAY_FILE):
    overlay = rename_section(read_ini_data(CALIBRATION_OVERLAY_FILE), "POCKETNC_FEATURES", "PENTA_FEATURES")
  else:
    overlay = { 'parameters': [],
                'sections': {} }

  before_features = merge_ini_data(defaults, overlay)
  merged = before_features

  features = set()
  priorities = {}

  # Auto detected features
  for feature in os.listdir(FEATURES_DIR):
    feature_path = os.path.join(FEATURES_DIR, feature)
    detect_path = os.path.join(feature_path, "detect")
    priority_path = os.path.join(feature_path, "priority")

    if os.path.isfile(detect_path) and os.access(detect_path, os.X_OK):
      detected = subprocess.check_output(detect_path).strip().decode("utf-8")
      if detected == "1":
        print("Detected feature, %s" % feature)
        features.add(feature)

    priorities[feature] = "1000"
    if os.path.isfile(priority_path) and os.access(priority_path, os.X_OK):
      priority = subprocess.check_output(priority_path).strip().decode("utf-8")
      priorities[feature] = priority

  # Manually enabled/disabled features
  for param in before_features['parameters']:
    section = param['values']['section']
    name = param['values']['name']
    value = param['values']['value']

    if section == "PENTA_FEATURES":
      feature = name.lower()
      if value == "1":
        features.add(feature)
      elif value == "0" and feature in features:
        features.remove(feature)
        
  for feature in sorted(features, key=lambda f: (float(priorities.get(f, "1000")), f)):
    dir = os.path.join(FEATURES_DIR, feature)

    feature_overlay_path = os.path.join(dir, "overlay.inc")
    feature_prepend_path = os.path.join(dir, "prepend.inc")
    feature_append_path = os.path.join(dir, "append.inc")
    feature_startup_path = os.path.join(dir, "startup")

    if os.path.isfile(feature_startup_path) and os.access(feature_startup_path, os.X_OK):
      # executed first so overlay.inc and/or append.inc could be generated by the script
      subprocess.check_output(feature_startup_path);

    if os.path.isfile(feature_overlay_path):
      feature_overlay = read_ini_data(feature_overlay_path)
      merged = merge_ini_data(merged, feature_overlay)

    if os.path.isfile(feature_append_path):
      feature_append = read_ini_data(feature_append_path)
      merged = append_ini_data(merged, feature_append)

    if os.path.isfile(feature_prepend_path):
      feature_prepend = read_ini_data(feature_prepend_path)
      merged = append_ini_data(feature_prepend, merged)

    merged = merge_ini_data(merged, {
      'parameters': [
        {
            'values': {
                'section': 'PENTA_FEATURES',
                'name': feature.upper(),
                'value': "1",
                'comment': '',
                'help': '',
                'default': ''
            }
        }
      ],
      'sections': {
          'PENTA_FEATURES': { 'comment': '', 'help': '' }
      }
    });

  merged = merge_ini_data(merged, overlay)

  if os.path.isfile(LAST_TOOL_FILE):
    last_tool = read_ini_data(LAST_TOOL_FILE)
  else:
    last_tool = { 'parameters': [],
                'sections': {} }

  merged = merge_ini_data(merged, last_tool)

  write_ini_data(merged, INI_FILE);
