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

START_IDX = 3
END_IDX = 102
BUCKET_SIZE = 5
BUCKET_TAG_SIZE = 1
PAGE_SIZE = 32


# EEPROM write will only occur when at least this many seconds have elapsed since previous write
WRITE_PERIOD = 3

def BytesToRuntime(bytes_arr):
  print(bytes_arr)
  if(len(bytes_arr) != BUCKET_SIZE - BUCKET_TAG_SIZE):
    raise ValueError("Runtime data should be 4 bytes, recieved: {0}".format(bytes_arr))
  r = 0
  i = 0
  for b in bytes_arr:
    r += b * pow(255,i)
    i += 1
  return r

def RuntimeToBytes(runtime):
  if runtime < 0 or runtime > 4294967296:
    raise ValueError("Runtime seconds must be in range [0, 2^32), recieved: {0}".format(runtime))
  arr = []
  for _ in list(range(4)):
    arr.append(runtime % 256)
    runtime = runtime // 256
  return arr

ee = eeprom.EEPROM()
data = ee.ReadBytes(START_IDX, END_IDX - START_IDX)
print(data)
latestBucketIdx = lastWriteTime = None

#Find the current position
if data[0] == 255:
  #This is a fresh EEPROM. Initialize
  ee.WriteBytes(START_IDX, [0] + RuntimeToBytes(0))
  latestBucketIdx = START_IDX
else:
  startTag = data[0]
  print('start tag {}'.format(startTag))
  for tagIdx in list(range(START_IDX,END_IDX,BUCKET_SIZE)):
    print(tagIdx)
    if(data[tagIdx - START_IDX] != startTag):
      #Found the first tag with different value than start tag
      #The preceeding bucket was the last written before shutdown
      latestBucketIdx = tagIdx - BUCKET_SIZE
      print('found latest idx {}'.format(latestBucketIdx))
      break
  if(latestBucketIdx is None):
    print('latest was last')
    #The last write before shutdown was in the final bucket
    latestBucketIdx = (END_IDX - BUCKET_SIZE) + 1

#find current value
# eepromIndex = START_IDX
# bucketValue = 0
# lastBucketValue = -1
# while eepromIndex < END_IDX and bucketValue > lastBucketValue:
#   lastBucketValue = bucketValue
#   bucketValue = rom.ReadBytes(eepromIndex,1)[0]
#   if bucketValue == 255:
#     break
#   else:
#     eepromIndex = eepromIndex + BUCKET_SIZE


# runtime = 0
# with open("/home/pocketnc/time","wb+") as f:
#   fc = f.read()
#   runtime = int(fc,2) if len(fc) > 0 else 0
# runtimeWritten = runtime
time.sleep(1)
print('bytes {}'.format(ee.ReadBytes(latestBucketIdx + 1, 4)))
time.sleep(1)
runtime = runtimeWritten = BytesToRuntime( ee.ReadBytes(latestBucketIdx + 1, 4) )
print('RUNTIME {}'.format(runtime))

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
        bucketIdx = (latestBucketIdx + BUCKET_SIZE) % (END_IDX - START_IDX + 1)
        print('writing to index {}'.format(bucketIdx))
        flag = ee.ReadBytes(bucketIdx,1)[0]
        print('current idx flag {}'.format(flag))
        newFlag = 1 if flag == 0 else 0
        time.sleep(0.1) #Wait a bit to keep I2C stable
        b = RuntimeToBytes(int(runtime))
        print('{}'.format(b))
        runtimeWritten = int(runtime)
        #If the write will cross EEPROM page boundary, split it up
        distFromGap = PAGE_SIZE - (bucketIdx % PAGE_SIZE)
        if(distFromGap < BUCKET_SIZE):
          print('splitting write {}'.format([newFlag] + RuntimeToBytes(runtimeWritten)[0:distFromGap - 1]))
          print('splitting write {}'.format(RuntimeToBytes(runtimeWritten)[ distFromGap - 1: ]))
          
          ee.WriteBytes( bucketIdx, [newFlag] + RuntimeToBytes(runtimeWritten)[0:distFromGap - 1])
          time.sleep(0.1)
          ee.WriteBytes( bucketIdx + distFromGap, RuntimeToBytes(runtimeWritten)[ distFromGap - 1: ])
        else:
          ee.WriteBytes( bucketIdx, [newFlag] + RuntimeToBytes(runtimeWritten))
        lastWriteTime = time.time()
        latestBucketIdx = bucketIdx
        # with open("/home/pocketnc/time","wb") as f:
        #   runtimeWritten = int(runtime)
        #   f.write(bin(runtimeWritten))
      except IOError as e:
        print(e)

except KeyboardInterrupt:
  raise SystemExit


'''
try:
  for i in list(range(0,102,4)):
    print(e.WriteBytes(i,[255]*4))
    print(i)
    time.sleep(0.1)
except IOError as ex:
  print('io error')
  print(ex)
except Exception as ex:
  print('gen error')
  print(ex)
'''