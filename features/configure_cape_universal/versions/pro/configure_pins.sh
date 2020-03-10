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
P8.7    in+     # B HLFB
P8.8    in+     # C HLFB
P8.9    in+     # X Limit
P8.10   in+     # E-Stop Signal
P8.11   out-    # C Dir
P8.12   out-    # C Step
P8.13   out     # Spindle PWM
P8.14   in+     # Y Limit
P8.15   out-    # Z Dir
P8.16   out-    # Z Step
P8.17   out     # E-Stop LED
P8.18   in+     # Z Limit
P8.19   in+     # C Limit
P8.26   in+     # Start Signal
P9.11   out+    # Spindle Dir
P9.12   out+    # Enable
P9.13   in+     # Y HLFB
P9.14   out-    # Start LED
P9.15   out-    # Y Dir
P9.16   in+     # B Limit
P9.17   in+     # Unused
P9.19   i2c     # I2C SCL
P9.20   i2c     # I2C SDA
P9.21   in+     # Interlock Open
P9.22   in+     # Probe Signal
P9.23   out-    # Y Step
P9.24   out+    # Spindle On
P9.25   in+     # X HLFB
P9.26   in+     # Z HLFB
P9.27   out-    # X Step
P9.28   out-    # B Dir
P9.29   out-    # X Dir
P9.30   out-    # B Step
EOF
