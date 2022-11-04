bb_gpio
=======

Sets up the bb_gpio HAL component so that Beaglebone Black and AI GPIO pins can be 
used in other features using instantiable components. Here's an example that creates
an enable-pin component that is bound to the GPIO pin connected to pin 12 of the P9 
header.

    newinst bb_gpio enable-pin pin=912 direction=output

After instantiating the enable-pin component, the enable-pin.out pin can be set to 1
to set the pin HIGH or 0 to set the pin LOW. Keep in mind that the enable-pin.out pin
is a HAL input, so HAL signals will drive a change on the pin.

Here is an input example:

    newinst bb_gpio x-limit-pin pin=809 direction=input
    setp x-limit-pin.invert 1

In this case, we're monitoring the GPIO pin connected to pin 9 on the P8 header. It's
connected to a limit switch that when triggered will short the pin to GND. Since we want
the logic to be HIGH when triggered and LOW otherwise, we set the x-limit-pin.invert to 1.
x-limit-pin.in will be set HIGH when the switch is triggered and LOW when it is not. Keep
in mind that the x-limit-pin.in is a HAL output, so it will drive the state of HAL signals.
