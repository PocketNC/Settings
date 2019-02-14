#!/usr/bin/python
import hal, time

h = hal.component("run_time_clock")
h.newpin("start", hal.HAL_BIT, hal.HAL_IN)
h.newpin("pause", hal.HAL_BIT, hal.HAL_IN)
h.newpin("reset", hal.HAL_BIT, hal.HAL_IO)
h.newpin("seconds", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

nowTime = time.time()
lastTime = nowTime
started = False

try:
    while True:
        time.sleep(.1)
        lastTime = nowTime
        nowTime = time.time()

        if h['reset']:
            h['seconds'] = 0
            h['reset'] = False
            started = False;

        elif not started: 
            if h['start'] or h['pause']:
                h['seconds'] = nowTime - lastTime;
                started = True
        
        elif not h['pause']:
            if h['start']:
                h['seconds'] = nowTime - lastTime + h['seconds']
            else:
                started = False
        

except KeyboardInterrupt:
    raise SystemExit
