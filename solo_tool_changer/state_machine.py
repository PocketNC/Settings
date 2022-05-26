from transitions import Machine
from enum import Enum, auto

# TODO - get these from configuration
X_MIN = -3.3736
X_MAX = 6.2312 
Y_MIN = -3.6487
Y_MAX = 3.7486
Z_MIN = -6.8746
B_MIN = -135
B_MAX = 45

EPS = .0001

SAFE_Z = -.1
SAFE_B = 0
SAFE_X = 1
TIME_ALLOWED_TO_OPEN_OR_CLOSE = 4

FAULT_FAILED_TO_CLOSE = -1
FAULT_FAILED_TO_OPEN = -2
FAULT_UNEXPECTED_NOT_CLOSED = -3
FAULT_UNEXPECTED_NOT_OPENED = -4

class States(Enum):
  STARTUP = auto()
  OK_TO_HOME = auto()
  NOT_CLOSED_AT_STARTUP = auto()
  CLOSE = auto()
  NOT_CLOSED = auto()
  FAULT = auto()
  NOT_OPENED = auto()
  OK_TO_CLOSE = auto()
  NOT_SAFE_TO_CLOSE = auto()
  OPEN = auto()
  OK_TO_OPEN = auto()
  NOT_SAFE_TO_OPEN = auto()
  PERFORMING_TOOL_CHANGE = auto()
  UNEXPECTED_NOT_CLOSED = auto()
  UNEXPECTED_NOT_OPENED = auto()

NEXT = "next"

class SoloToolChangerState(object):
  def __init__(self, h):
    self.h = h

    self.last_open_cmd = False
    self.last_close_cmd = False
    self.last_clamp_cmd = False
    
    self.machine = Machine(self, states=States, initial=States.STARTUP, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.STARTUP, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")
    self.machine.add_transition(NEXT, States.STARTUP, States.NOT_CLOSED_AT_STARTUP, unless="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.OK_TO_HOME, States.NOT_SAFE_TO_OPEN, conditions="is_homed")
    self.machine.add_transition(NEXT, States.OK_TO_HOME, States.UNEXPECTED_NOT_CLOSED, unless="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.NOT_SAFE_TO_OPEN, unless="is_safe_to_open")
    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.OPEN, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.STARTUP, unless="is_homed")
    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.UNEXPECTED_NOT_CLOSED, unless="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_OPEN, States.OK_TO_OPEN, conditions="is_safe_to_open")
    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_OPEN, States.STARTUP, unless="is_homed")
    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_OPEN, States.UNEXPECTED_NOT_CLOSED, unless="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.OPEN, States.OK_TO_CLOSE, conditions="is_opened_sensor_triggered")
    self.machine.add_transition(NEXT, States.OPEN, States.NOT_OPENED, conditions="has_drawer_timed_out")
    self.machine.add_transition(NEXT, States.OPEN, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.PERFORMING_TOOL_CHANGE, conditions="is_tool_change_requested")
    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.NOT_SAFE_TO_CLOSE, unless="is_safe_to_close")
    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.CLOSE, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.STARTUP, unless="is_homed")
#    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.UNEXPECTED_NOT_OPENED, unless="is_opened_sensor_triggered")

    self.machine.add_transition(NEXT, States.PERFORMING_TOOL_CHANGE, States.NOT_SAFE_TO_CLOSE, unless="is_tool_change_requested")
    self.machine.add_transition(NEXT, States.PERFORMING_TOOL_CHANGE, States.STARTUP, unless="is_homed")
#    self.machine.add_transition(NEXT, States.PERFORMING_TOOL_CHANGE, States.UNEXPECTED_NOT_OPENED, unless="is_opened_sensor_triggered")

    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_CLOSE, States.OK_TO_CLOSE, conditions="is_safe_to_close")
    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_CLOSE, States.STARTUP, unless="is_homed")
#    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_CLOSE, States.UNEXPECTED_NOT_OPENED, unless="is_opened_sensor_triggered")

    self.machine.add_transition(NEXT, States.CLOSE, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")
    self.machine.add_transition(NEXT, States.CLOSE, States.NOT_CLOSED, conditions="has_drawer_timed_out")

    self.machine.add_transition(NEXT, States.NOT_CLOSED_AT_STARTUP, States.CLOSE, conditions="has_user_indicated_safe_to_close")
    self.machine.add_transition(NEXT, States.NOT_CLOSED_AT_STARTUP, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.FAULT, States.STARTUP)

    self.time_since_open_or_close = 0

  def update(self, dt):
    self.time_since_open_or_close += dt
    
    self.last_open_cmd = self.h["open-cmd"]
    self.last_close_cmd = self.h["close-cmd"]
    self.last_clamp_cmd = self.h["clamp-cmd"]
    self.last_unclamp_cmd = self.h["unclamp-cmd"]

  def resetTime(self):
    self.time_since_open_or_close = 0

  def on_enter_PERFORMING_TOOL_CHANGE(self):
    print("PERFORMING_TOOL_CHANGE")
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0

  def on_enter_NOT_CLOSED_AT_STARTUP(self):
    print("NOT_CLOSED_AT_STARTUP")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0

  def on_enter_STARTUP(self):
    print("STARTUP")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0

  def on_enter_OPEN(self):
    print("OPEN")
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS

  def on_enter_CLOSE(self):
    print("CLOSE")
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS

  def on_enter_OK_TO_HOME(self):
    print("OK_TO_HOME")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_OK_TO_OPEN(self):
    print("OK_TO_OPEN")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_NOT_SAFE_TO_OPEN(self):
    print("NOT_SAFE_TO_OPEN")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_OK_TO_CLOSE(self):
    print("OK_TO_CLOSE")
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS


  def on_enter_NOT_SAFE_TO_CLOSE(self):
    print("NOT_SAFE_TO_CLOSE")
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS 

  def on_enter_UNEXPECTED_NOT_CLOSED(self):
    print("UNEXPECTED_NOT_CLOSED")
    print("Tool changer drawer started to open unexpectedly.")
    self.h["fault-reason"] = FAULT_UNEXPECTED_NOT_CLOSED
    self.to_FAULT()

  def on_enter_UNEXPECTED_NOT_OPENED(self):
    print("UNEXPECTED_NOT_OPENED")
    print("Tool changer drawer started to close unexpectedly.")
    self.h["fault-reason"] = FAULT_UNEXPECTED_NOT_OPENED
    self.to_FAULT()

  def on_enter_NOT_OPENED(self):
    print("NOT_OPENED")
    print("Failed to open tool changer drawer")
    self.h["fault-reason"] = FAULT_FAILED_TO_OPEN
    self.to_FAULT()

  def on_enter_NOT_CLOSED(self):
    print("NOT_CLOSED")
    print("Failed to close tool changer drawer")
    self.h["fault-reason"] = FAULT_FAILED_TO_CLOSE
    self.to_FAULT()

  def on_enter_FAULT(self):
    print("FAULT")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = True
    self.h["b-min"] = -EPS

  @property
  def has_user_indicated_safe_to_close(self):
    return self.h["safe-to-close"]

  @property
  def has_drawer_timed_out(self):
    return (
      self.time_since_open_or_close > TIME_ALLOWED_TO_OPEN_OR_CLOSE and
      ((not self.is_closed_sensor_triggered and self.state == States.CLOSE) or
      (not self.is_opened_sensor_triggered and self.state == States.OPEN))
    )

  @property
  def is_clamp_requested(self):
# these edge triggers cause issues when the command was given in a state that doesn't allow a transition

#    return self.h["clamp-cmd"] and self.h["clamp-cmd"] != self.last_clamp_cmd
    return self.h["clamp-cmd"]

  @property
  def is_unclamp_requested(self):
#    return self.h["unclamp-cmd"] and self.h["unclamp-cmd"] != self.last_unclamp_cmd
    return self.h["unclamp-cmd"]

  @property
  def is_open_requested(self):
    # open is requested on rising edge only
#    return self.h["open-cmd"] and self.h["open-cmd"] != self.last_open_cmd
    return self.h["open-cmd"]

  @property
  def is_close_requested(self):
#    return self.h["close-cmd"] and self.h["close-cmd"] != self.last_close_cmd
    return self.h["close-cmd"]

  @property
  def is_closed_sensor_triggered(self):
    return self.h["closed-sensor"]

  @property
  def is_opened_sensor_triggered(self):
    return self.h["opened-sensor"]
  
  @property
  def is_homed(self):
    return (
      self.h["x-homed"] and 
      self.h["y-homed"] and 
      self.h["z-homed"] and 
      self.h["b-homed"]
    )

  @property
  def is_safe_to_open(self):
    return (
      self.h["x-homed"] and
      self.h["y-homed"] and
      self.h["z-homed"] and
      self.h["b-homed"] and
      (self.h["x-position"] <= SAFE_X+EPS or
       self.h["z-position"] >= SAFE_Z-EPS) and
      self.h["b-position"] >= SAFE_B-EPS
    )

  @property
  def is_safe_to_close(self):
    return self.is_safe_to_open

  @property
  def is_tool_change_requested(self):
    return self.is_safe_to_open and self.h["tool-change-cmd"]
