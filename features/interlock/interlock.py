#!/usr/bin/python

import hal
import os
import time
import logging

logging.basicConfig(filename='/var/log/hal.log',format='%(asctime)sZ pid:%(process)s module:%(module)s %(message)s', level=logging.ERROR)

progAlertIssued = False
spindleAlertIssued = False

h = hal.component('interlock')

h.newpin('closed', hal.HAL_BIT, hal.HAL_IN)
h.newpin('prog-running', hal.HAL_BIT, hal.HAL_IN)
h.newpin('program-is-paused', hal.HAL_BIT, hal.HAL_IN)
h.newpin('spindle-is-on', hal.HAL_BIT, hal.HAL_IN)
h.newpin('mode-is-mdi', hal.HAL_BIT, hal.HAL_IN)

h.newpin('feature-enabled', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('pause-prog', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-inhibit', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-resume', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-paused-by-interlock', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('exception', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('prog-alert', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('exception-alert', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-alert', hal.HAL_BIT, hal.HAL_OUT)

h['feature-enabled'] = True
h['pause-prog'] = False
h['spindle-inhibit'] = False
h['spindle-resume'] = False
h['spindle-paused-by-interlock'] = False
h['exception'] = False
h['exception-alert'] = False
h['prog-alert'] = False
h['spindle-alert'] = False

h.ready()

try:
  while True:
    try:
      h['exception'] = False
      if not ( h['program-is-paused'] or (h['mode-is-mdi'] and h['spindle-is-on']) ):
          h['spindle-paused-by-interlock'] = False

      if h['closed']:
        if not h['spindle-paused-by-interlock']:
          h['spindle-inhibit'] = False
          spindleAlertIssued = False

        if h['spindle-resume']:
          h['spindle-paused-by-interlock'] = False
          h['spindle-inhibit'] = False
          h['spindle-resume'] = False

        h['pause-prog'] = False
        progAlertIssued = False
      else:
        if h['spindle-is-on']:
          h['spindle-paused-by-interlock'] = True
          if not spindleAlertIssued:
            spindleAlertIssued = True
            h['spindle-alert'] = True
        h['spindle-inhibit'] = True
        if h['prog-running']:
          h['pause-prog'] = True
          if not progAlertIssued:
            progAlertIssued = True
            h['prog-alert'] = True
        elif h['program-is-paused']:
          #set pause-prog pin False so it is ready next time it is needed (it's effect occurs when changing state from False to True)
          h['pause-prog'] = False
          #once Rockhopper has issued alerts, be ready to issue alert again in case an attempt is made to start a program without first closing the interlock
          progAlertIssued = h['prog-alert']

    except Exception as e:
      print 'Exception in interlock component: %s' % (e)
      logging.error(e)
      h['exception'] = True
      h['exception-alert'] = True
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit