#!/usr/bin/python 

from copy import deepcopy
import os
import re
import pprint
import sys

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
from ini import read_ini_data, merge_ini_data, write_ini_data


INI_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini")
INI_DEFAULT_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini.default")
CALIBRATION_OVERLAY_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/CalibrationOverlay.inc")

if __name__ == "__main__":
    defaults = read_ini_data(INI_DEFAULT_FILE)

    if os.path.isfile(CALIBRATION_OVERLAY_FILE):
        overlay = read_ini_data(CALIBRATION_OVERLAY_FILE)
    else:
        overlay = { 'parameters': [],
                    'sections': {} }

    merged = merge_ini_data(defaults, overlay)

    write_ini_data(merged, INI_FILE);
