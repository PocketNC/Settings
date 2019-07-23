#!/usr/bin/python

import hal
import os
import time
import logging

logging.basicConfig(filename='/var/log/hal.log',format='%(asctime)sZ pid:%(process)s module:%(module)s %(message)s', level=logging.ERROR)

pauseAlertIssued = False
waitForSpindlePeriod = 2 # How long to wait for spindle to spin up before resuming motion

h = hal.component('interlock')

h.newpin('closed', hal.HAL_BIT, hal.HAL_IN)
h.newpin('program-running', hal.HAL_BIT, hal.HAL_IN)
h.newpin('program-is-paused', hal.HAL_BIT, hal.HAL_IN)
h.newpin('spindle-is-on', hal.HAL_BIT, hal.HAL_IN)
h.newpin('mode-is-mdi', hal.HAL_BIT, hal.HAL_IN)
h.newpin('current-vel', hal.HAL_FLOAT, hal.HAL_IN)
h.newpin('start-button-pulse', hal.HAL_BIT, hal.HAL_IN)

h.newpin('release', hal.HAL_BIT, hal.HAL_IO)

h.newpin('pause-program', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('resume-program', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-inhibit', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('feed-inhibit', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('spindle-stop', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('program-paused-by-interlock', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('program-paused-by-interlock.not', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('pause-alert', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('exception', hal.HAL_BIT, hal.HAL_OUT)
h.newpin('exception-alert', hal.HAL_BIT, hal.HAL_OUT)

h['pause-program'] = False
h['resume-program'] = False
h['spindle-inhibit'] = False
h['feed-inhibit'] = False
h['spindle-stop'] = False
h['program-paused-by-interlock'] = False
h['program-paused-by-interlock.not'] = True
h['pause-alert'] = False
h['exception'] = False
h['exception-alert'] = False

h.ready()

try:
  while True:
    try:
      h['pause-program'] = False
      h['resume-program'] = False
      h['spindle-stop'] = False
      h['pause-alert'] = False
      h['exception'] = False
      h['exception-alert'] = False
      h['program-paused-by-interlock.not'] =  not h['program-paused-by-interlock']

      if not ( h['program-is-paused'] or ( h['mode-is-mdi'] and h['spindle-is-on'] ) ):
          h['program-paused-by-interlock'] = False
          h['feed-inhibit'] = False

      if h['closed']:
        if not h['program-paused-by-interlock']:
          h['spindle-inhibit'] = False
          h['feed-inhibit'] = False

        if h['release']:
          h['program-paused-by-interlock'] = False
          h['spindle-inhibit'] = False
          startTime = time.time()
          # Wait a bit so spindle is up to speed before motion resumes
          while True:
            elapsedTime = time.time() - startTime
            if elapsedTime > waitForSpindlePeriod or not h['closed']:
              break
          h['feed-inhibit'] = False
          h['release'] = False
        elif h['start-button-pulse'] and h['program-paused-by-interlock']:
          h['program-paused-by-interlock'] = False
          h['spindle-inhibit'] = False
          startTime = time.time()
          # Wait a bit so spindle is up to speed before motion resumes
          while True:
            elapsedTime = time.time() - startTime
            if elapsedTime > waitForSpindlePeriod or not h['closed']:
              break
          h['feed-inhibit'] = False
          h['resume-program'] = True
          #necessary to wait here, signal propagation seems to vary and sometimes take longer than 10ms
          while h['program-is-paused']:
            time.sleep(.001)

        pauseAlertIssued = False
      else:
        if h['program-running']:
          h['pause-program'] = True
          while abs(h['current-vel']) > 0.0001 :
            time.sleep(0.001)
          h['feed-inhibit'] = True
          h['program-paused-by-interlock'] = True
          if not pauseAlertIssued:
            pauseAlertIssued = True
            h['pause-alert'] = True
        elif h['program-is-paused']:
          # We do want to set feed-inhibit and program-paused-by-interlock True here, because the program could already be paused when the interlock is opened
          h['feed-inhibit'] = True
          h['program-paused-by-interlock'] = True
          #set pause-program pin False so it is ready next time it is needed (it's effect occurs when changing state from False to True)
          h['pause-program'] = False
          #once Rockhopper has issued alert, be ready to issue alert again in case an attempt is made to start a program without first closing the interlock
          pauseAlertIssued = h['pause-alert']
        elif h['spindle-is-on']:
          #This propagates through to halui.spindle-stop, and is necessary to prevent the spindle from resuming automatically when interlock closes
          h['spindle-stop'] = True

        h['spindle-inhibit'] = True
        h['release'] = False

    except Exception as e:
      print 'Exception in interlock component: %s' % (e)
      logging.error(e)
      h['exception'] = True
      h['exception-alert'] = True
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit