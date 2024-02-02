#!/bin/bash

dummy_pid=$(pgrep dummy.sh)
until [ -n "$dummy_pid" ]; do
  echo "Waiting for dummy.sh before continuing..."
  dummy_pid=$(pgrep dummy.sh)
  sleep 1
done

ini_pin_data=$(halcmd show pin ini | grep ini -m 1)
while [ -z "$ini_pin_data" ]; do
  echo "Waiting for ini pin before continuing..."
  sleep 5
  ini_pin_data=$(halcmd show pin ini | grep ini -m 1)
done


sleep 1
halcmd -f /opt/pocketnc/Settings/versions/solo/PocketNC_PostMillTask.hal

sleep 1

python3 /opt/pocketnc/Settings/versions/solo/set_default_max_velocity.py

sleep 10
halcmd -f /opt/pocketnc/Settings/versions/solo/resetMaxTimes.hal
