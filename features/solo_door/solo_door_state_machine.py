from transitions import Machine
from enum import Enum, auto
import json

TIME_ALLOWED_TO_OPEN_OR_CLOSE = 10
EPS = .0001

DELAY = .5

class States(Enum):
  STARTUP = auto()
  UP = auto()
  DOWN_LID_OPENED = auto()
  DOWN_LID_CLOSED = auto()
  UNCERTAIN = auto()
  OPENING = auto()
  CLOSING = auto()
  RUNNING = auto()
  TIMEOUT_OPENING_DOOR = auto()
  TIMEOUT_CLOSING_DOOR = auto()
  UNEXPECTED_DOOR_NOT_CLOSED = auto()
  FAULT = auto()

def int_to_solo_door_state(i):
  return States(i).name

NEXT = "next"

FAULT_TIMEOUT_OPENING_DOOR = -1
FAULT_TIMEOUT_CLOSING_DOOR = -2
FAULT_UNEXPECTED_DOOR_NOT_CLOSED = -3

class SoloDoorState(object):
  def __init__(self, h, messageClient):
    self.h = h
    self.messageClient = messageClient
    self.time_since_open_or_close = 0
    self.enteredRunning = False

    self.doorSensorTimes = [ 0, 0, 0, 0 ]
    self.door_sensor_1 = 0
    self.door_sensor_2 = 0

    self.warnedSpindleOn = False
    self.warnedCuttingFluidIsOn = False
    self.warnedRunning = False
    self.warnedNoClose = False

    self.machine = Machine(self, states=States, initial=States.STARTUP, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.STARTUP, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.STARTUP, States.DOWN_LID_OPENED, conditions="is_door_down_lid_opened")
    self.machine.add_transition(NEXT, States.STARTUP, States.DOWN_LID_CLOSED, conditions="is_door_down_lid_closed")
    self.machine.add_transition(NEXT, States.STARTUP, States.UNCERTAIN, conditions="is_door_uncertain")

    self.machine.add_transition(NEXT, States.UP, States.CLOSING, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.UP, States.UNCERTAIN, conditions="is_door_uncertain")

    self.machine.add_transition(NEXT, States.DOWN_LID_OPENED, States.DOWN_LID_CLOSED, conditions="is_door_down_lid_closed")

    self.machine.add_transition(NEXT, States.DOWN_LID_CLOSED, States.DOWN_LID_OPENED, conditions="is_door_down_lid_opened")
    self.machine.add_transition(NEXT, States.DOWN_LID_CLOSED, States.OPENING, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.DOWN_LID_CLOSED, States.RUNNING, conditions="is_running")

    self.machine.add_transition(NEXT, States.RUNNING, States.UNEXPECTED_DOOR_NOT_CLOSED, unless="is_door_down")
    self.machine.add_transition(NEXT, States.RUNNING, States.UP, conditions="is_door_up_and_not_running")
    self.machine.add_transition(NEXT, States.RUNNING, States.DOWN_LID_OPENED, conditions="is_door_down_lid_opened_and_not_running")
    self.machine.add_transition(NEXT, States.RUNNING, States.DOWN_LID_CLOSED, conditions="is_door_down_lid_closed_and_not_running")
    self.machine.add_transition(NEXT, States.RUNNING, States.UNCERTAIN, conditions="is_door_uncertain_and_not_running")

    # repeatedly transition back to the same state to evaluate warnings in the on_enter_RUNNING method
    self.machine.add_transition(NEXT, States.RUNNING, States.RUNNING)

    self.machine.add_transition(NEXT, States.UNCERTAIN, States.OPENING, conditions="is_open_requested")
# We may not want to allow closing from an uncertain state. If the door is tilted back, triggering the close solenoid
# will result in there not being any support for the door in the up position when manually tilting it back. 
# In either a tilted state or a partially open state, we can safely engage the open solenoid, so we may want that to
# be the only option we allow in order to get back to a known state. 
#    self.machine.add_transition(NEXT, States.UNCERTAIN, States.CLOSING, conditions="is_close_requested_and_not_tilted")
    self.machine.add_transition(NEXT, States.UNCERTAIN, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.UNCERTAIN, States.DOWN_LID_OPENED, conditions="is_door_down_lid_opened")
    self.machine.add_transition(NEXT, States.UNCERTAIN, States.DOWN_LID_CLOSED, conditions="is_door_down_lid_closed")

    # repeatedly transition back to the same state to evaluate warnings in the on_enter_UNCERTAIN method
    self.machine.add_transition(NEXT, States.UNCERTAIN, States.UNCERTAIN)

    self.machine.add_transition(NEXT, States.OPENING, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.OPENING, States.CLOSING, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.OPENING, States.TIMEOUT_OPENING_DOOR, conditions="has_timed_out")

    self.machine.add_transition(NEXT, States.CLOSING, States.DOWN_LID_CLOSED, conditions="is_door_down_lid_closed")
    self.machine.add_transition(NEXT, States.CLOSING, States.DOWN_LID_OPENED, conditions="is_door_down_lid_opened")
    self.machine.add_transition(NEXT, States.CLOSING, States.OPENING, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.CLOSING, States.TIMEOUT_CLOSING_DOOR, conditions="has_timed_out")

    self.machine.add_transition(NEXT, States.FAULT, States.STARTUP, conditions="is_reset_requested")

  def update(self, dt):
    self.time_since_open_or_close += dt

    # decrement all times by dt, but don't go less than 0
    self.doorSensorTimes[0] = max(0, self.doorSensorTimes[0]-dt)
    self.doorSensorTimes[1] = max(0, self.doorSensorTimes[1]-dt)
    self.doorSensorTimes[2] = max(0, self.doorSensorTimes[2]-dt)
    self.doorSensorTimes[3] = max(0, self.doorSensorTimes[3]-dt)

    rawDoorSensorData = (self.h["door-sensor-1"] << 1) | self.h["door-sensor-2"]

    # add 2*dt for the current raw state to compensate for the fact that we decremented the active one as well above
    # Between this line and the decrements above, we're essentially saying increment the active state and decrement all the others.
    self.doorSensorTimes[rawDoorSensorData] = min(self.doorSensorTimes[rawDoorSensorData]+2*dt, DELAY)

    try:
      # When one state reaches DELAY, change the state
      filteredDoorSensorData = self.doorSensorTimes.index(DELAY)

      self.door_sensor_1 = not not (filteredDoorSensorData & 2)
      self.door_sensor_2 = not not (filteredDoorSensorData & 1)
      self.h["door-sensor-1-out"] = self.door_sensor_1
      self.h["door-sensor-2-out"] = self.door_sensor_2
    except:
      # otherwise, don't do anything
      pass

  def resetTime(self):
    self.time_since_open_or_close = 0

  def on_enter_STARTUP(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 0

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1

  def on_enter_UP(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 1
    self.h["close-out"] = 0
    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1


  def on_enter_DOWN_LID_OPENED(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 1

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.max-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.max-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.max-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.max-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.max-velocity"]
    self.h["inhibit-spindle"] = 0
    self.h["inhibit-cutting-fluid"] = 0

  def on_enter_DOWN_LID_CLOSED(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 1

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.max-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.max-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.max-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.max-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.max-velocity"]
    self.h["inhibit-spindle"] = 0
    self.h["inhibit-cutting-fluid"] = 0

  def on_enter_UNCERTAIN(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 0

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1

    if self.h["close-cmd"]:
      if not self.warnedNoClose:
        self.warnedNoClose = True
        self.messageClient.send(json.dumps({
          "type": "warning",
          "kind": "solo-door",
          "text": "Must first open door in case door is up and tilted back."
        }))
    else:
      self.warnedNoClose = False

  def on_enter_OPENING(self):
    self.resetTime()
    self.h["state"] = self.state.value
    self.h["open-out"] = 1
    self.h["close-out"] = 0

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1

  def on_enter_CLOSING(self):
    self.resetTime()
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 1

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1

  def on_enter_RUNNING(self):
    self.h["state"] = self.state.value
    self.h["open-out"] = 0
    self.h["close-out"] = 1

    self.h["fault"] = 0
    self.h["fault-reason"] = 0
    self.h["joint.0.max-velocity-out"] = self.h["joint.0.max-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.max-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.max-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.max-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.max-velocity"]
    self.h["inhibit-spindle"] = 0
    self.h["inhibit-cutting-fluid"] = 0

    if self.h["open-cmd"]:
      if self.h["spindle-on"] and not self.warnedSpindleOn:
        self.warnedSpindleOn = True
        self.messageClient.send(json.dumps({
          "type": "warning",
          "kind": "solo-door",
          "text": "Cannot open door while spindle is on."
        }))

      if self.h["cutting-fluid-is-on"] and not self.warnedCuttingFluidIsOn:
        self.warnedCuttingFluidIsOn = True
        self.messageClient.send(json.dumps({
          "type": "warning",
          "kind": "solo-door",
          "text": "Cannot open door while coolant is on."
        }))

      if self.h["running"] and not self.warnedRunning:
        self.warnedRunning = True
        self.messageClient.send(json.dumps({
          "type": "warning",
          "kind": "solo-door",
          "text": "Cannot open door while interpreter is running."
        }))
    else:
      self.warnedSpindleOn = False
      self.warnedCuttingFluidIsOn = False
      self.warnedRunning = False



  def on_enter_TIMEOUT_OPENING_DOOR(self):
    self.h["fault-reason"] = FAULT_TIMEOUT_OPENING_DOOR
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-door",
      "text": "Door failed to open within %s seconds." % (TIME_ALLOWED_TO_OPEN_OR_CLOSE, )
    }))
    self.to_FAULT()

  def on_enter_TIMEOUT_CLOSING_DOOR(self):
    self.h["fault-reason"] = FAULT_TIMEOUT_CLOSING_DOOR
    self.to_FAULT()

  def on_enter_UNEXPECTED_DOOR_NOT_CLOSED(self):
    self.h["fault-reason"] = FAULT_UNEXPECTED_DOOR_NOT_CLOSED
    self.messageClient.send(json.dumps({
      "type": "error",
      "kind": "solo-door",
      "text": "Door unexpectedly started to open."
    }))
    self.to_FAULT()

  def on_enter_FAULT(self):
    self.h["state"] = self.state.value
    self.h["fault"] = 1
    self.h["open-out"] = 0
    self.h["close-out"] = 0

    self.h["joint.0.max-velocity-out"] = self.h["joint.0.open-velocity"]
    self.h["joint.1.max-velocity-out"] = self.h["joint.1.open-velocity"]
    self.h["joint.2.max-velocity-out"] = self.h["joint.2.open-velocity"]
    self.h["joint.3.max-velocity-out"] = self.h["joint.3.open-velocity"]
    self.h["joint.4.max-velocity-out"] = self.h["joint.4.open-velocity"]
    self.h["inhibit-spindle"] = 1
    self.h["inhibit-cutting-fluid"] = 1

  @property
  def is_door_up_and_not_running(self):
    return self.is_door_up and not self.is_running

  @property
  def is_door_down_lid_closed_and_not_running(self):
    return self.is_door_down_lid_closed and not self.is_running

  @property
  def is_door_down_lid_opened_and_not_running(self):
    return self.is_door_down_lid_opened and not self.is_running

  @property
  def is_door_uncertain_and_not_running(self):
    return self.is_door_uncertain and not self.is_running

  @property
  def is_door_up(self):
    return not self.door_sensor_1 and self.door_sensor_2

  @property
  def is_door_down_lid_closed(self):
    return self.door_sensor_1 and self.door_sensor_2

  @property
  def is_door_down_lid_opened(self):
    return self.door_sensor_1 and not self.door_sensor_2

  @property
  def is_door_down(self):
    return self.door_sensor_1

  @property
  def is_door_uncertain(self):
    return not self.door_sensor_1 and not self.door_sensor_2

  @property
  def has_timed_out(self):
    return (
      self.time_since_open_or_close > TIME_ALLOWED_TO_OPEN_OR_CLOSE and
      (self.state == States.CLOSING or self.state == States.OPENING)
    )

  @property
  def is_open_requested(self):
    return self.h["open-cmd"]

  @property
  def is_close_requested(self):
    return self.h["close-cmd"]

  @property
  def is_running(self):
    return self.h["running"] or self.h["spindle-on"] or self.h["cutting-fluid-is-on"]

  @property
  def is_reset_requested(self):
    return self.h["reset-cmd"]
