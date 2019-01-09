#!/bin/bash

dtbo_err () {
  echo "Error loading device tree overlay file: $DTBO" >&2
  exit 1
}

SLOTS=/sys/devices/bone_capemgr.*/slots

# Make sure required device tree overlay(s) are loaded
for DTBO in PocketNCdriver cape-bone-iio ; do
  if grep -q $DTBO $SLOTS ; then
    echo $DTBO overlay found
  else
    echo Loading $DTBO overlay
    sudo -A su -c "echo $DTBO > $SLOTS" || dtbo_err
    sleep 1
  fi
done;
