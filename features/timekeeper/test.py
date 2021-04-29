#!/usr/bin/python
import unittest
import time
import eeprom
import timekeeper_core

unittest.TestLoader.sortTestMethodsUsing = None

START_IDX = timekeeper_core.START_IDX
END_IDX = timekeeper_core.END_IDX
PAGE_SIZE = timekeeper_core.PAGE_SIZE    
TAG_SIZE = timekeeper_core.TAG_SIZE
DATA_SIZE = timekeeper_core.DATA_SIZE
BUCKET_SIZE = timekeeper_core.BUCKET_SIZE
MAX_DATA_VAL = timekeeper_core.MAX_DATA_VAL
WRITE_PERIOD = 0.1 # = timekeeper_core.WRITE_PERIOD
REST_PERIOD = timekeeper_core.REST_PERIOD
TOTAL_SIZE = timekeeper_core.TOTAL_SIZE

ee = eeprom.EEPROM()

class TestTimekeeper(unittest.TestCase):
  maxDiff = None

  def test_1_bytes_conversion(self):
    self.assertEqual( [0] * DATA_SIZE, timekeeper_core.runtime_to_bytes(0) )
    self.assertEqual( 0, timekeeper_core.bytes_to_runtime( [0] * DATA_SIZE) )
    self.assertEqual( pow(2,8 * DATA_SIZE) - 1, timekeeper_core.bytes_to_runtime([255] * DATA_SIZE) )
    self.assertEqual( 0, timekeeper_core.bytes_to_runtime( timekeeper_core.runtime_to_bytes(0) ) )
    self.assertEqual( 1, timekeeper_core.bytes_to_runtime( timekeeper_core.runtime_to_bytes(1) ) )
    self.assertEqual( 255, timekeeper_core.bytes_to_runtime( timekeeper_core.runtime_to_bytes(255) ) )
    self.assertEqual( 256, timekeeper_core.bytes_to_runtime( timekeeper_core.runtime_to_bytes(256) ) )

  def test_2_eeprom_module_read(self):
    try:
      b = ee.ReadBytes(START_IDX, END_IDX + 1 - START_IDX)
      time.sleep(REST_PERIOD)
      self.assertEqual( END_IDX + 1 - START_IDX, len(b) )
    except Exception as ex:
      self.fail("Reading EEPROM raised exception unexpectedly! {0}".format(ex))

  def test_3_eeprom_module_write(self):
    try:
      b = ee.WriteBytes(START_IDX, [0])
      time.sleep(REST_PERIOD)
    except Exception as ex:
      self.fail("Writing to EEPROM raised exception unexpectedly! {0}".format(ex))

  def test_4_reset_and_initialize_interface(self):
    try:
      ee.WriteBytes( START_IDX, ( PAGE_SIZE - (START_IDX % PAGE_SIZE) ) * [255] )
      time.sleep(REST_PERIOD)
      loopStart = START_IDX + PAGE_SIZE - (START_IDX % PAGE_SIZE)
      for i in range(loopStart, END_IDX, PAGE_SIZE):
        #SMBus appears to be bugged, when a list of 32 ints is sent
        #There is an error saying the list must be "not more than 32 integers"
        ee.WriteBytes(i, (PAGE_SIZE - 1) * [255] )
        time.sleep(REST_PERIOD)
        ee.WriteBytes(i + PAGE_SIZE - 1, [255] )
        time.sleep(REST_PERIOD)
      eeArr = ee.ReadBytes(START_IDX, (END_IDX - START_IDX + 1))
      time.sleep(REST_PERIOD)
      self.assertEqual([255] * TOTAL_SIZE, eeArr)
    except Exception as ex:
      self.fail("Resetting EEPROM to 1s raised exception unexpectedly! {0}".format(ex))
    try:
      interface = timekeeper_core.EEPROMInterface()
      self.assertEqual([0] * BUCKET_SIZE, ee.ReadBytes(START_IDX,BUCKET_SIZE))
    except Exception as ex:
      self.fail("Initializing interface raised exception unexpectedly! {0}".format(ex))

  def test_5_start_and_write_once(self):
    try:
      interface = timekeeper_core.EEPROMInterface()
      time.sleep(REST_PERIOD)
      interface.write_next(1)
      time.sleep(REST_PERIOD)
      self.assertEqual(
        [0] * BUCKET_SIZE + [0,1] + (DATA_SIZE - 1) * [0], 
        ee.ReadBytes(START_IDX, BUCKET_SIZE*2)
      )
    except Exception as ex:
      self.fail("Initializing interface raised exception unexpectedly! {0}".format(ex))
    
  def test_6_start_and_write_another_150_times(self):
    '''
    We start in in a state where the first 2 buckets hold values 0 and 1. 
    All other bytes in the EEPROM block are 255
    We will write 10,000 times
    The final bucket will be ((START + 2) + 10,000) % NUMBER_OF_BUCKETS
    The final value will be 10,000
    The rest of the EEPROM block should contain the preceeding values between:
    (10,000 - NUMBER_OF_BUCKETS) and (10,000 - 1)
    
    The flag values should be 0 or 1, and all flags of the same value should
    be in a contiguous block that stretches to at least one boundary (left or right)
    The value of the first bucket's flag will be 0 if ((2 + 10,000) / NUMBER_OF_BUCKETS) is an even number
    or the flag will be 1 if ((2 + 10,000) / LENGTH) is an odd number.
    Flags after the first bucket up to and including the final position will have the same value
    as the first bucket's flag.
    Flags to the right of the final position will have the other value (0 or 1)
    If the final position is the right-most bucket, all flags will have the same value
    '''
    try:
      interface = timekeeper_core.EEPROMInterface()
      time.sleep(REST_PERIOD)
      for i in list(range(2,150 + 2)):
        interface.write_next(i)  
        time.sleep(REST_PERIOD)

      numBuckets = TOTAL_SIZE / BUCKET_SIZE
      finalFlagFirstBucket = 0 if (((1 + 150) / numBuckets) % 2) == 0 else 1
      finalBucketIdx = START_IDX + ((1 + 150) * BUCKET_SIZE) % TOTAL_SIZE
      finalBytes = []
      listOfBucketsWithFirstBucketFlag = list(enumerate(range(finalBucketIdx, START_IDX -1, -BUCKET_SIZE)))
      for i, bucketIdx in listOfBucketsWithFirstBucketFlag:
        finalBytes = [finalFlagFirstBucket] + timekeeper_core.runtime_to_bytes(150 + 1 - i) + finalBytes
      if finalBucketIdx < (END_IDX - BUCKET_SIZE):
        otherFinalFlag = 0 if finalFlagFirstBucket == 1 else 1
        for i, bucketIdx in list(enumerate(range(finalBucketIdx + BUCKET_SIZE, END_IDX, BUCKET_SIZE))):
          finalBytes = finalBytes + [otherFinalFlag] + timekeeper_core.runtime_to_bytes(150 + 2 - numBuckets + i)

      self.assertEqual(
        finalBytes,
        ee.ReadBytes(START_IDX, TOTAL_SIZE)
      )
    except Exception as ex:
      self.fail("Initializing interface raised exception unexpectedly! {0}".format(ex))
