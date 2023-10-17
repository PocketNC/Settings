VERSION = "dev"
HOSTNAME = "trinket"

LOOP_TIMING = 0.005 # in seconds
# How often are we querying the pin states

DEBOUNCE_TIME = 0.5 # in seconds
# In non-continuous mode, this is the amount of time that is required 
# for a shift in pin value to be considered a change. For instance:
# if a pin sends a True, False, True, False over the course of 
# 50ms and the DEBOUNCE_TIME is set to 100ms, the only change that will
# be reported is the initial True since the subsequent pulses occurred
# within the 100ms window
