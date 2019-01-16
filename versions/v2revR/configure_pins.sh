#!/bin/bash

while read PIN DIR JUNK ; do
  case "$PIN" in
    ""|\#*)	
      continue 
      ;;
    *)
      echo config-pin $PIN $DIR
      config-pin $PIN $DIR
      ;;
  esac

done <<- EOF
P8.8    in-     # Spindle Clock
P8.9    in+     # X Limit
P8.10   in+     # E-Stop Signal
P8.11   out-    # B Dir
P8.12   out-    # B Step
P8.13   out     # Spindle PWM
P8.14   in+     # Y Limit
P8.15   out-    # Z Dir
P8.16   out-    # Z Step
P8.17   out     # E-Stop LED
P8.18   in+     # Z Limit
P8.19   in+     # B Limit
P8.26   in+     # Start Signal
P9.11   out+    # Spindle Dir
P9.12   out+    # Enable
P9.14   out-    # Start LED
P9.15   out-    # Y Dir
P9.16   in+     # A Limit
P9.17   in+     # Unused
P9.19   i2c     # I2C SCL
P9.20   i2c     # I2C SDA
P9.22   in+     # Probe Signal
P9.23   out-    # Y Step
P9.24   out+    # Spindle On
P9.27   out-    # X Step
P9.28   out-    # A Dir
P9.29   out-    # X Dir
P9.30   out-    # A Step
EOF
