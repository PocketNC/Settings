#!/usr/bin/python3

from transitions import Machine
from enum import Enum, auto
import time
import traceback
import hal
import json
import penta_messages
import os

class States(Enum):
  NORMAL = auto()
  STOP_SPINDLE = auto()
  INHIBITED = auto()
  CLOSED = auto()
  SPIN_UP = auto()

NEXT = "next"

STOP_SPINDLE_DURATION = .1
SPIN_UP_DURATION = 3

# inputs
RUNNING_PIN = "running"
PAUSED_PIN = "paused"
IDLE_PIN = "idle"
OPEN_PIN = "open"
SPINDLE_ON_PIN = "spindle-on"

# outputs
STATE_PIN = "state"
STOP_SPINDLE_PIN = "stop-spindle"
FEED_HOLD_PIN = "feed-hold"
INHIBIT_FEED_PIN = "inhibit-feed"
INHIBIT_SPINDLE_PIN = "inhibit-spindle"
OK_TO_RUN_PIN = "ok-to-run"

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

def send_spindle_stopped_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "interlock", 
    "text": "Enclosure opened while spindle enabled. Spindle has been stopped.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_inhibited_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "interlock", 
    "text": "Enclosure opened while program is running. Program has been paused.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

class InterlockState:
  def __init__(self, h):
    self.h = h

    self.machine = Machine(self, states=States, initial=States.NORMAL, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.NORMAL, States.STOP_SPINDLE, conditions="should_spindle_be_stopped", after=send_spindle_stopped_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited", after=send_inhibited_message)

    self.machine.add_transition(NEXT, States.STOP_SPINDLE, States.NORMAL, conditions="stopped_spindle_for_enough_time")

    self.machine.add_transition(NEXT, States.INHIBITED, States.STOP_SPINDLE, conditions="machine_is_idle")
    self.machine.add_transition(NEXT, States.INHIBITED, States.CLOSED, conditions="safety_switch_is_closed")

    self.machine.add_transition(NEXT, States.CLOSED, States.INHIBITED, conditions="safety_switch_is_opened")
    self.machine.add_transition(NEXT, States.CLOSED, States.STOP_SPINDLE, conditions="machine_is_idle")
    self.machine.add_transition(NEXT, States.CLOSED, States.SPIN_UP, conditions="machine_is_running")

    self.machine.add_transition(NEXT, States.SPIN_UP, States.INHIBITED, conditions="safety_switch_is_opened", after=send_inhibited_message)
    self.machine.add_transition(NEXT, States.SPIN_UP, States.NORMAL, conditions="spun_up_for_enough_time")

  @property
  def machine_is_running(self):
    return self.h[RUNNING_PIN]

  @property
  def safety_switch_is_opened(self):
    return self.h[OPEN_PIN]

  @property
  def safety_switch_is_closed(self):
    return not self.h[OPEN_PIN]

  @property
  def machine_is_idle(self):
    return self.h[IDLE_PIN]

  @property
  def should_machine_be_inhibited(self):
    return (
      (self.h[RUNNING_PIN] and self.h[OPEN_PIN]) or
      (self.h[PAUSED_PIN] and self.h[SPINDLE_ON_PIN] and self.h[OPEN_PIN])
    )

  @property
  def should_spindle_be_stopped(self):
    # this really only needs to be long enough to properly trigger a spindle-stop-# signal
    return (
      (self.h[IDLE_PIN] and self.h[SPINDLE_ON_PIN] and self.h[OPEN_PIN])
    )

  @property
  def stopped_spindle_for_enough_time(self):
    return (time.time() - self.stopped_spindle_at > STOP_SPINDLE_DURATION)

  @property
  def spun_up_for_enough_time(self):
    return (time.time() - self.spin_up_started_at > SPIN_UP_DURATION)

  def on_enter_STOP_SPINDLE(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = True
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = False
    self.stopped_spindle_at = time.time()

  def on_enter_NORMAL(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_INHIBITED(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = True
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False

  # Should transition to CLOSED state after being inhibited and the safty switch is closed
  def on_enter_CLOSED(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_SPIN_UP(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True
    self.spin_up_started_at = time.time()

if __name__ == "__main__":
  h = hal.component('interlock')
  h.newpin(RUNNING_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(PAUSED_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(IDLE_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(OPEN_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(SPINDLE_ON_PIN, hal.HAL_BIT, hal.HAL_IN)

  h.newpin(STATE_PIN, hal.HAL_S32, hal.HAL_OUT)
  h.newpin(STOP_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(FEED_HOLD_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_FEED_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(OK_TO_RUN_PIN, hal.HAL_BIT, hal.HAL_OUT)

  h[STATE_PIN] = States.NORMAL.value
  h[STOP_SPINDLE_PIN] = False
  h[FEED_HOLD_PIN] = False
  h[INHIBIT_FEED_PIN] = False
  h[INHIBIT_SPINDLE_PIN] = False
  h[OK_TO_RUN_PIN] = True

  state = InterlockState(h)
  h.ready()

  try:
    while True:
      state.next()
      time.sleep(.01)
  except KeyboardInterrupt:
    raise SystemExit
