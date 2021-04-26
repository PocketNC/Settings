#!/usr/bin/python


START_IDX = 3 # The boundaries of the continuous chunk of EEPROM used by this component.
END_IDX = 102 
PAGE_SIZE = 32 # EEPROM page size
TAG_SIZE = 1 # Number of bytes for a tag
DATA_SIZE = 4 # Number of bytes for each runtime written to EEPROM
BUCKET_SIZE = TAG_SIZE + DATA_SIZE
MAX_DATA_VAL = pow(2, DATA_SIZE * 8)
WRITE_PERIOD = 10 # Minimum number of seconds between EEPROM writes
TOTAL_SIZE = END_IDX - START_IDX + 1