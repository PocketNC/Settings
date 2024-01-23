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

halcmd -f /opt/pocketnc/Settings/features/beta_solo_door/solo_door_post_milltask.hal
