#!/usr/bin/python

import hal
import os
import time
import logging

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

logging.basicConfig(filename='/var/log/hal.log',format='%(asctime)sZ pid:%(process)s module:%(module)s %(message)s', level=logging.ERROR)


progAlertIssued = False
spindleAlertIssued = False

try:
  while True:
    try:
      if not ( h['program-is-paused'] or (h['mode-is-mdi'] and h['spindle-is-on']) ):
          h['spindle-paused-by-interlock'] = False

      if h['closed']:
        if not h['spindle-paused-by-interlock']:
          h['spindle-inhibit'] = False

        if h['spindle-resume']:
          h['spindle-paused-by-interlock'] = False
          h['spindle-inhibit'] = False
          h['spindle-resume'] = False

        h['pause-prog'] = False
        spindleAlertIssued = False
        progAlertIssued = False

      else:
        if h['spindle-is-on']:
          h['spindle-paused-by-interlock'] = True
          if not spindleAlertIssued:
            spindleAlertIssued = True
            h['spindle-alert'] = True
        h['spindle-inhibit'] = True
        if h['prog-running']:
          # the pause-prog pin must go from low to high to trigger a pause, and seems to take some time to switch statesd
          h['pause-prog'] = False
          while h['pause-prog']:
            time.sleep(0.001)
          h['pause-prog'] = True
          if not progAlertIssued:
            progAlertIssued = True
            h['prog-alert'] = True

    except Exception as e:
      print 'Exception in interlock component: %s' % (e)
      logging.error(e)
      h['exception'] = True
      h['exception-alert'] = True
      #Sleep for a second so only one exception alert is issued
      time.sleep(1)
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit