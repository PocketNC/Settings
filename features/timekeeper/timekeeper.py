#!/usr/bin/python
import hal, time
import logging
import logging.config
import uuid
import os
import struct
import sys
sys.path.append('/home/pocketnc/pocketnc/Settings')
import eeprom
import constants

START_IDX = constants.START_IDX
END_IDX = constants.END_IDX
PAGE_SIZE = constants.PAGE_SIZE
TAG_SIZE = constants.TAG_SIZE
DATA_SIZE = constants.DATA_SIZE
BUCKET_SIZE = constants.BUCKET_SIZE
MAX_DATA_VAL = constants.MAX_DATA_VAL
WRITE_PERIOD = constants.WRITE_PERIOD
TOTAL_SIZE = constants.TOTAL_SIZE

def BytesToRuntime(bytes_arr):
  if(len(bytes_arr) != BUCKET_SIZE - TAG_SIZE):
    raise ValueError("Runtime data should be {0} bytes, recieved: {1}".format((BUCKET_SIZE - TAG_SIZE), bytes_arr) )
  r = 0
  i = 0
  for b in bytes_arr:
    r += b * pow(256,i)
    i += 1
  return r

def RuntimeToBytes(runtime):
  if runtime < 0 or runtime > MAX_DATA_VAL:
    raise ValueError("Runtime seconds must be in range [0, 2^{0}), recieved: {1}".format(8 * DATA_SIZE,runtime))
  arr = []
  for _ in list(range(4)):
    arr.append(runtime % 256)
    runtime = runtime // 256
  return arr

ee = eeprom.EEPROM()

#Read current EEPROM state
ee_arr = ee.ReadBytes(START_IDX, (END_IDX + 1) - START_IDX)
time.sleep(0.1)

#Find the current position
if ee_arr[0] == 255:
  #This is a fresh EEPROM. Initialize
  ee.WriteBytes(START_IDX, [0] + RuntimeToBytes(0))
  time.sleep(0.1)
  latestBucketIdx = START_IDX
else:
  startTag = ee_arr[0]
  for tagIdx in list(range(START_IDX, END_IDX + 1, BUCKET_SIZE)):
    if(ee_arr[tagIdx - START_IDX] != startTag):
      #Found the first tag with different value than start tag
      #The preceeding bucket was the last written before shutdown
      latestBucketIdx = tagIdx - BUCKET_SIZE
      break
  if(latestBucketIdx is None):
    #End bucket was the last bucket written before shutdown
    latestBucketIdx = (END_IDX - BUCKET_SIZE) + 1

runtime = runtimeWritten = BytesToRuntime( ee.ReadBytes(latestBucketIdx + 1, 4) )

now = time.time()
last = now
lastWriteTime = now

h = hal.component("timekeeper")
h.newpin("spindle-on", hal.HAL_BIT, hal.HAL_IN)
h.ready()

try:
  while True:
    time.sleep(1)
    last = now
    now = time.time()

    if h['spindle-on']:
      runtime += (now - last)
      
    if(int(runtime) != runtimeWritten and (now - lastWriteTime) > WRITE_PERIOD):
      try:
        bucketIdx = (latestBucketIdx + BUCKET_SIZE) % ((END_IDX + 1) - START_IDX)
        flag = ee.ReadBytes(bucketIdx,1)[0]
        time.sleep(0.1)
        newFlag = 1 if flag == 0 else 0
        b = RuntimeToBytes(int(runtime))
        runtimeWritten = int(runtime)
        #If the write will cross EEPROM page boundary, split it up
        distFromGap = PAGE_SIZE - (bucketIdx % PAGE_SIZE)
        if(distFromGap < BUCKET_SIZE):          
          ee.WriteBytes( bucketIdx, [newFlag] + RuntimeToBytes(runtimeWritten)[0:distFromGap - 1])
          time.sleep(0.1)
          ee.WriteBytes( bucketIdx + distFromGap, RuntimeToBytes(runtimeWritten)[ distFromGap - 1: ])
        else:
          ee.WriteBytes( bucketIdx, [newFlag] + RuntimeToBytes(runtimeWritten))
        lastWriteTime = time.time()
        latestBucketIdx = bucketIdx
      except IOError as e:
        print(e)

except KeyboardInterrupt:
  raise SystemExit

