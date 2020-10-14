#!/bin/bash

pin_err () {
  echo "Error exporting pin:$PIN" >&2
  exit 1
}

dir_err () {
  echo "Error setting direction:$DIR on pin:$PIN" >&2
  exit 1
}

interrupt_err () {
  echo "Error setting interrupt" >&2
  exit 1
}

# Export GPIO pins:
# One pin needs to be exported to enable the low-level clocks for the GPIO
# modules (there is probably a better way to do this)
# 
# Any GPIO pins driven by the PRU need to have their direction set properly
# here.  The PRU does not do any setup of the GPIO, it just yanks on the
# pins and assumes you have the output enables configured already
# 
# Direct PRU inputs and outputs do not need to be configured here, the pin
# mux setup (which is handled by the device tree overlay) should be all
# the setup needed.
# 
# Any GPIO pins driven by the hal_bb_gpio driver do not need to be
# configured here.  The hal_bb_gpio module handles setting the output
# enable bits properly.  These pins _can_ however be set here without
# causing problems.  You may wish to do this for documentation or to make
# sure the pin starts with a known value as soon as possible.

while read PIN DIR JUNK ; do
        case "$PIN" in
        ""|\#*)	
		continue ;;
        *)
	if [ ! -r /sys/class/gpio/gpio$PIN ]; then
          sudo -A su -c "echo $PIN > /sys/class/gpio/export" || pin_err
        fi
        sudo -A su -c "echo $DIR > /sys/class/gpio/gpio$PIN/direction" || dir_err
                ;;
        esac

done <<- EOF
	178	in	# P8.9		gpio6.18	X Limit
	164	in	# P8.10		gpio6.4		E-Stop 5V Connected
	107	in	# P8.13		gpio4.11	E-Stop GND Connected
	109	in	# P8.14		gpio4.13	Y Limit
	242	out	# P8.17		gpio8.18	E-Stop LED
	 22	out	# P8.23		gpio1.22	X Enable
	192	in	# P8.24		gpio7.0 	I2C Expander Interrupt 1A
	191	in	# P8.25		gpio6.31 	I2C Expander Interrupt 2A
	124	in	# p8.26		gpio4.28	Start Signal
	119	in	# p8.27		gpio8.19	Tool Changer Open
	115	in	# p8.28		gpio4.19	Tool Changer Closed
	118	in	# p8.29		gpio4.22	Tool Changer Home
	238	out	# p8.31		gpio8.14	Y Enable
	239	out	# p8.32		gpio8.15	Tool Changer Enable
	236	out	# p8.35		gpio8.12	Z Enable
	230	out	# p8.39		gpio8.6	        B Enable
	226	out	# p8.43		gpio8.2	        C Enable
	128	out	# p9.12		gpio5.0 	Enable
	121	out	# p9.14		gpio4.25	Start LED
	122	in	# p9.16		gpio4.26	B Limit
	203	in	# p9.23		gpio7.11	Interlock 2
	175	in	# P9.24		gpio6.15	Probe 1 Signal
	177	in	# P9.25		gpio6.17	Probe 2 Signal
	111	in	# P9.27		gpio4.15	Z Limit
	113	in	# P9.28		gpio4.17	C Limit
	139	in	# p9.29		gpio5.11        Interlock
EOF

#sudo -A su -c "echo rising > /sys/class/gpio/gpio67/edge" || interrupt_err # set interrupt on p8.8 
