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
	165	in	# P8.7		gpio6.5		B Feedback
	166	in	# P8.8		gpio6.6		Spindle Clock
	178	in	# P8.9		gpio6.18	X Limit
	164	in	# P8.10		gpio6.4		E-Stop Signal
	75	in	# P8.11		gpio3.11	B Dir - V2
	74	in	# P8.12		gpio3.10	B Step - V2
	107	out	# P8.13		gpio4.11	Spindle PWM
	109	in	# P8.14		gpio4.13	Y Limit
	99	in	# P8.15		gpio4.3 	Z Dir - V2
	125	in	# P8.16		gpio4.29	Z Step - V2
	242	out	# P8.17		gpio8.18	E-Stop LED
	105	in	# P8.18		gpio4.9		Z Limit
	106	in	# P8.19		gpio4.10	B Limit
	124	in	# p8.26		gpio4.28	Start Signal
	119	in	# p8.27		gpio8.19	C Feedback
	118	in	# p8.30		gpio4.20	Y Feedback
	241	out	# p9.11		gpio8.17	Spindle Dir
	128	out	# p9.12		gpio5.0 	Enable
	172	in	# p9.13		gpio6.12	Y Feedback - not connected
	121	out	# p9.14		gpio4.25	Start LED
	76	in	# p9.15		gpio3.12	Y Dir - V2
	122	in	# p9.16		gpio4.26	A Limit
	209	in	# p9.17		gpio7.17	Unused
	67	in	# p9.21		gpio3.3		Interlock
	179	in	# p9.22		gpio6.19	Probe Signal
	203	in	# p9.23		gpio7.11	Y Step - V2
	175	out	# P9.24		gpio6.15	Spindle On
	177	in	# P9.25		gpio6.17	X Feedback
	174	in	# P9.26		gpio6.14	Z Feedback
	111	in	# P9.27		gpio4.15	X Step - V2
	113	in	# P9.28		gpio4.17	A Dir - V2
	139	in	# p9.29		gpio5.11        X Dir - V2
	140	in	# p9.30		gpio5.12	A Step - V2
EOF

sudo -A su -c "echo rising > /sys/class/gpio/gpio67/edge" || interrupt_err # set interrupt on p8.8 
