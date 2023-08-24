from transitions import Machine
from enum import Enum, auto
import penta_messages
import ini
import os

POCKETNC_VAR_DIRECTORY = os.environ["POCKETNC_VAR_DIRECTORY"]

INI_DATA = ini.read_ini_data(os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini"))

X_MIN = float(ini.get_parameter(INI_DATA, 'JOINT_0', 'MIN_LIMIT')['values']['value'])
X_MAX = float(ini.get_parameter(INI_DATA, 'JOINT_0', 'MAX_LIMIT')['values']['value'])
Y_MIN = float(ini.get_parameter(INI_DATA, 'JOINT_1', 'MIN_LIMIT')['values']['value'])
Y_MAX = float(ini.get_parameter(INI_DATA, 'JOINT_1', 'MAX_LIMIT')['values']['value'])
Z_MIN = float(ini.get_parameter(INI_DATA, 'JOINT_2', 'MIN_LIMIT')['values']['value'])
B_MIN = float(ini.get_parameter(INI_DATA, 'JOINT_3', 'MIN_LIMIT')['values']['value'])
B_MAX = float(ini.get_parameter(INI_DATA, 'JOINT_3', 'MAX_LIMIT')['values']['value'])

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
  def __init__(self, h, messageClient):
    self.h = h
    self.messageClient = messageClient

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
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_NOT_CLOSED_AT_STARTUP(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_STARTUP(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_OPEN(self):
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_CLOSE(self):
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_OK_TO_HOME(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_OK_TO_OPEN(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN
    self.h["ok-to-close"] = True
    self.h["ok-to-open"] = True

  def on_enter_NOT_SAFE_TO_OPEN(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_OK_TO_CLOSE(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS
    self.h["ok-to-close"] = True
    self.h["ok-to-open"] = True


  def on_enter_NOT_SAFE_TO_CLOSE(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS 
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

  def on_enter_UNEXPECTED_NOT_CLOSED(self):
    self.h["fault-reason"] = FAULT_UNEXPECTED_NOT_CLOSED
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-tool-changer",
      "text": "Tool changer started to open unexpectedly."
    }))
    self.to_FAULT()

  def on_enter_UNEXPECTED_NOT_OPENED(self):
    self.h["fault-reason"] = FAULT_UNEXPECTED_NOT_OPENED
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-tool-changer",
      "text": "Tool changer started to close unexpectedly."
    }))
    self.to_FAULT()

  def on_enter_NOT_OPENED(self):
    self.h["fault-reason"] = FAULT_FAILED_TO_OPEN
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-tool-changer",
      "text": "Tool changer failed to open within %s seconds." % (TIME_ALLOWED_TO_OPEN_OR_CLOSE ,)
    }))
    self.to_FAULT()

  def on_enter_NOT_CLOSED(self):
    self.h["fault-reason"] = FAULT_FAILED_TO_CLOSE
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-tool-changer",
      "text": "Tool changer failed to close within %s seconds." % (TIME_ALLOWED_TO_OPEN_OR_CLOSE ,)
    }))
    self.to_FAULT()

  def on_enter_FAULT(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = True
    self.h["b-min"] = -EPS
    self.h["ok-to-close"] = False
    self.h["ok-to-open"] = False

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
