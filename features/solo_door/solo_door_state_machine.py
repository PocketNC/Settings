from transitions import Machine
from enum import Enum, auto
import json

EPS = .0001

DELAY = .5

class States(Enum):
  STARTUP = auto()
  UP = auto()
  DOWN = auto()
  PARTIALLY_OPEN = auto()
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

    self.warnedSpindleOn = False
    self.warnedCuttingFluidIsOn = False
    self.warnedRunning = False
    self.warnedNoClose = False

    self.machine = Machine(self, states=States, initial=States.STARTUP, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.STARTUP, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.STARTUP, States.DOWN, conditions="is_door_down")
    self.machine.add_transition(NEXT, States.STARTUP, States.PARTIALLY_OPEN, conditions="is_door_partially_open")

    self.machine.add_transition(NEXT, States.UP, States.CLOSING, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.UP, States.PARTIALLY_OPEN, conditions="is_door_partially_open")

    self.machine.add_transition(NEXT, States.DOWN, States.UNEXPECTED_DOOR_NOT_CLOSED, unless="is_door_down")
    self.machine.add_transition(NEXT, States.DOWN, States.OPENING, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.DOWN, States.RUNNING, conditions="is_running")

    self.machine.add_transition(NEXT, States.RUNNING, States.UNEXPECTED_DOOR_NOT_CLOSED, unless="is_door_down")
    self.machine.add_transition(NEXT, States.RUNNING, States.UP, conditions="is_door_up_and_not_running")
    self.machine.add_transition(NEXT, States.RUNNING, States.DOWN, conditions="is_door_down_and_not_running")
    self.machine.add_transition(NEXT, States.RUNNING, States.PARTIALLY_OPEN, conditions="is_door_partially_open_and_not_running")

    # repeatedly transition back to the same state to evaluate warnings in the on_enter_RUNNING method
    self.machine.add_transition(NEXT, States.RUNNING, States.RUNNING)

    self.machine.add_transition(NEXT, States.PARTIALLY_OPEN, States.OPENING, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.PARTIALLY_OPEN, States.CLOSING, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.PARTIALLY_OPEN, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.PARTIALLY_OPEN, States.DOWN, conditions="is_door_down")

    self.machine.add_transition(NEXT, States.OPENING, States.UP, conditions="is_door_up")
    self.machine.add_transition(NEXT, States.OPENING, States.CLOSING, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.OPENING, States.TIMEOUT_OPENING_DOOR, conditions="has_timed_out")
    self.machine.add_transition(NEXT, States.OPENING, States.PARTIALLY_OPEN, conditions="is_stop_requested")

    self.machine.add_transition(NEXT, States.CLOSING, States.DOWN, conditions="is_door_down")
    self.machine.add_transition(NEXT, States.CLOSING, States.OPENING, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.CLOSING, States.TIMEOUT_CLOSING_DOOR, conditions="has_timed_out")
    self.machine.add_transition(NEXT, States.CLOSING, States.PARTIALLY_OPEN, conditions="is_stop_requested")

    self.machine.add_transition(NEXT, States.FAULT, States.STARTUP)

  def update(self, dt):
    self.time_since_open_or_close += dt

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

  def on_enter_DOWN(self):
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

  def on_enter_PARTIALLY_OPEN(self):
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
      "text": "Door failed to open within %s seconds." % (self.h["timeout"], )
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
  def is_door_down_and_not_running(self):
    return self.is_door_down and not self.is_running

  @property
  def is_door_partially_open_and_not_running(self):
    return self.is_door_partially_open and not self.is_running

  @property
  def is_door_up(self):
    return self.h["door-up-sensor"]

  @property
  def is_door_down(self):
    return self.h["door-down-sensor"]

  @property
  def is_door_partially_open(self):
    return not self.is_door_down and not self.is_door_up

  @property
  def is_timeout_enabled(self):
    return self.h["timeout-enabled"]

  @property
  def is_stop_requested(self):
    return self.h["stop-cmd"]

  @property
  def has_timed_out(self):
    return (
      self.time_since_open_or_close > self.h["timeout"] and
      (self.state == States.CLOSING or self.state == States.OPENING) and
      self.is_timeout_enabled
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
