#!/bin/bash

sleep 1
halcmd -f /opt/pocketnc/Settings/versions/solo/PocketNC_PostMillTask.hal

sleep 10
halcmd -f /opt/pocketnc/Settings/versions/solo/resetMaxTimes.hal
