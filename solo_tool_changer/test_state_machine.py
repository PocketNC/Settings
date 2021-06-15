from state_machine import SoloToolChangerState

h = {}
h["open-cmd"] = False
h["closed-sensor"] = False
h["opened-sensor"] = False
h["b-position"] = -90
h["x-position"] = 4.5
h["y-position"] = 0
h["z-position"] = -6
h["b-min"] = -135
h["x-homed"] = False
h["y-homed"] = False
h["z-homed"] = False
h["b-homed"] = False
h["open-out"] = False
h["close-out"] =  False
h["inhibit-feed"] = False
h["inhibit-homing"] = True
h["fault"] = False
h["fault-reason"] = False

state = SoloToolChangerState(h)
