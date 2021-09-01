#!/bin/bash


# This python script resets the linuxcnc interpreter so that status values are
# refetched, this is a workaround to an issue with incorrect initial values for
# work offset status values: g5x_index, g5x_offset, g92_offset
# It is run here so that this always occurs during linuxcnc startup
# but after all other startup steps have finished.
linuxcnc-python ${POCKETNC_DIRECTORY}/Settings/reset_interpreter.py

echo Started dummy display!
sleep infinity
