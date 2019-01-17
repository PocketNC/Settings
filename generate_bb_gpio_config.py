#!/usr/bin/python

import sys
import os

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"

sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Rockhopper"));
sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Settings"));

from ini import read_ini_data, merge_ini_data, write_ini_data, append_ini_data, set_parameter

overlay_path = sys.argv[1]
output_overlay_path = sys.argv[2]

overlay = read_ini_data(overlay_path)

short_values = {}
inputs = []
outputs = []
for param in overlay['parameters']:
  name = param['values']['name']
  value = param['values']['value']
  if name.endswith("_SHORT"):
    short_values[name.replace("_SHORT", "")] = value

  if "in" in value and name.endswith("_LONG"):
    inputs.append(name.replace("_LONG", ""))

  if "out" in value and name.endswith("_LONG"):
    outputs.append(name.replace("_LONG", ""))

bb_gpio_config = "hal_bb_gpio output_pins=%s input_pins=%s" % (",".join([ short_values[o] for o in outputs ]),
                                                               ",".join([ short_values[i] for i in inputs ]))

set_parameter(overlay, "POCKETNC_PINS", "BB_GPIO_CONFIG", bb_gpio_config)

write_ini_data(overlay, output_overlay_path)
