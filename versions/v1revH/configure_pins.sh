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
P8.9    in+     # X Limit
P8.11   out     # X Dir
P8.12   out-    # X Step
P8.13   out     # Spindle PWM
P8.14   in+     # Y Limit
P8.15   out-    # Y Dir
P8.16   out-    # Y Step
P8.18   in+     # Z Limit
P8.19   in+     # B Limit
P9.11   out+    # Spindle Dir
P9.12   out+    # Enable
P9.15   out-    # Z Step
P9.16   in+     # A Limit
P9.22   in+     # Start
P9.23   out-    # Z Dir
P9.24   out+    # Spindle On
P9.27   out-    # A Step
P9.28   out-    # A Dir
P9.29   out-    # B Step
P9.30   out-    # B Dir
EOF
