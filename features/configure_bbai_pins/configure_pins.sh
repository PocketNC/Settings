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
	166	in	# P8.8		gpio2.3		Spindle Clock
	178	in	# P8.9		gpio2.5		X Limit
	164	in	# P8.10		gpio2.4		E-Stop Signal
	75	out	# P8.11		gpio1.13	B Dir
	74	out	# P8.12		gpio1.12	B Step
	107	out	# P8.13		gpio0.23	Spindle PWM
	109	in	# P8.14		gpio0.26	Y Limit
	99	out	# P8.15		gpio1.15	Z Dir
	125	out	# P8.16		gpio1.14	Z Step
	242	out	# P8.17		gpio0.27	E-Stop LED
	105	in	# P8.18		gpio2.1		Z Limit
	106	in	# P8.19		gpio0.22	B Limit
	124	in	# p8.26		gpio1.29	Start Signal
	241	out	# p9.11		gpio0.30	Spindle Dir
	128	out	# p9.12		gpio1.28	Enable
	121	out	# p9.14		gpio1.18	Start LED
	76	out	# p9.15		gpio1.16	Y Dir
	122	in	# p9.16		gpio1.19	A Limit
	209	in	# p9.17		gpio0.5		Unused
	67	in	# p9.21		gpio0.3		Interlock
	179	in	# p9.22		gpio0.2		Probe Signal
	203	out	# p9.23		gpio1.17	Y Step
	175	out	# P9.24		gpio0.15	Spindle On
	111	out	# P9.27		gpio3.19	X Step
	113	out	# P9.28		gpio3.17	A Dir
	139	out	# p9.29		gpio3.15        X Dir
	140	out	# p9.30		gpio3.16	A Step
EOF

sudo -A su -c "echo rising > /sys/class/gpio/gpio67/edge" || interrupt_err # set interrupt on p8.8 
