#!/bin/sh

VERSION=`./version.py`

dtc -O dtb -o PocketNCdriver-00A0.dtbo -b 0 -@ versions/$VERSION/PocketNCdriver-00A0.dts && \
cp PocketNCdriver-00A0.dtbo /lib/firmware/

