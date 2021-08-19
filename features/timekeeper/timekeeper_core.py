#!/usr/bin/python3
import hal, os, time
import eeprom

POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')

START_IDX = 13 # The boundaries of the continuous chunk of EEPROM used by this component.
END_IDX = 112 
TOTAL_SIZE = END_IDX - START_IDX + 1

DATA_SIZE = 4 # Number of bytes for each runtime written to EEPROM
TAG_SIZE = 1 # Number of bytes for a tag
BUCKET_SIZE = TAG_SIZE + DATA_SIZE

MAX_DATA_VAL = 1 << (DATA_SIZE * 8)  - 1

WRITE_PERIOD = 10 # Minimum number of seconds between EEPROM writes
REST_PERIOD = 0.01 # Use this to set sleep duration after EEPROM read/writes
PAGE_SIZE = 32 # EEPROM page size

def bytes_to_runtime(bytes_arr):
  if(len(bytes_arr) != BUCKET_SIZE - TAG_SIZE):
    raise ValueError("Runtime data should be {0} bytes, recieved: {1}".format((BUCKET_SIZE - TAG_SIZE), bytes_arr) )
  r = 0
  i = 0
  for b in bytes_arr:
    r += b << (i*8)
    i += 1
  return r

def runtime_to_bytes(runtime):
  if runtime < 0 or runtime > MAX_DATA_VAL:
    raise ValueError("Runtime seconds must be in range [0, 2^{0}), recieved: {1}".format(8 * DATA_SIZE,runtime))
  arr = []
  for _ in list(range(4)):
    arr.append(runtime % 256)
    runtime = runtime // 256
  return arr

class EEPROMInterface:
  def __init__(self):
    self.ee = eeprom.EEPROM()
    self.latestBucketIdx = None
    self.find_position()
    self.runtime = bytes_to_runtime( self.ee.ReadBytes(self.latestBucketIdx + 1, DATA_SIZE) )

  def find_position(self):
    ee_arr = self.ee.ReadBytes(START_IDX, (END_IDX + 1) - START_IDX)
    time.sleep(REST_PERIOD)
    self.position = None
    if ee_arr[0] == 255:
      #This is a fresh EEPROM.
      self.ee.WriteBytes(START_IDX, [0] + runtime_to_bytes(0))
      time.sleep(REST_PERIOD)
      self.latestBucketIdx = START_IDX
    else:
      startTag = ee_arr[0]
      for tagIdx in list(range(START_IDX, END_IDX + 1, BUCKET_SIZE)):
        if(ee_arr[tagIdx - START_IDX] != startTag):
          #Found the first tag with different value than start tag
          #The preceeding bucket was the last written before shutdown
          self.latestBucketIdx = tagIdx - BUCKET_SIZE
          break
      if(self.latestBucketIdx is None):
        #End bucket was the last bucket written before shutdown
        self.latestBucketIdx = (END_IDX - BUCKET_SIZE) + 1

  def write_next(self, timeVal):
    try:
      bucketIdx = (self.latestBucketIdx + BUCKET_SIZE - START_IDX) % (TOTAL_SIZE) + START_IDX
      flag = self.ee.ReadBytes(bucketIdx,1)[0]
      time.sleep(REST_PERIOD)
      newFlag = 1 if flag == 0 else 0
      timeBytes = runtime_to_bytes(int(timeVal))
      #If the write will cross EEPROM page boundary, split it up
      distFromGap = PAGE_SIZE - (bucketIdx % PAGE_SIZE)
      if(distFromGap < BUCKET_SIZE):
        self.ee.WriteBytes( bucketIdx, [newFlag] + timeBytes[0:distFromGap - 1])
        time.sleep(REST_PERIOD)
        self.ee.WriteBytes( bucketIdx + distFromGap, timeBytes[ distFromGap - 1: ])
      else:
        self.ee.WriteBytes( bucketIdx, [newFlag] + timeBytes)
      self.latestBucketIdx = bucketIdx
      self.runtime = int(timeVal)
    except IOError as e:
      print(e)

class FilesystemInterface:
  def __init__(self):
    self.runtime = self.get_runtime()
    self.filepath = os.path.join(POCKETNC_VAR_DIRECTORY, ".time")

  def get_runtime(self):
    mode = 'rb' if os.path.exists(self.filepath) else 'wb'
    with open(self.filepath, mode) as f:
      fc = f.read()
      return int.from_bytes(fc,'little') if len(fc) > 0 else 0

  def write_next(self, timeVal):
    with open(self.filepath, "wb") as f:
      writeVal = int(timeVal)
      f.write((writeVal).to_bytes(4, byteorder='little', signed=False))
      self.runtime = writeVal
