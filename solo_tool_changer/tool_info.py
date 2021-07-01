import math
from state_machine import EPS

# these are taken from and must match the tool change G code subroutines
TOOL_1_X = 6.2153
TOOL_1_Y = 2.9225
TOOL_1_Z = -6.1170
TOOL_DIST = 40.75 / 25.4
MIDDLE_OFFSET_X =  math.sqrt(3) * .5 * TOOL_DIST
MIDDLE_OFFSET_Y = .5 * TOOL_DIST

TOOL_SETTER_POSITION = ( TOOL_1_X - MIDDLE_OFFSET_X, TOOL_1_Y - MIDDLE_OFFSET_Y )

TOOL_POSITIONS = [
  ( TOOL_1_X, TOOL_1_Y, TOOL_1_Z ),
  ( TOOL_1_X, TOOL_1_Y - TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X, TOOL_1_Y - 2*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X, TOOL_1_Y - 3*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X, TOOL_1_Y - 4*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - MIDDLE_OFFSET_X, TOOL_1_Y - MIDDLE_OFFSET_Y - TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - MIDDLE_OFFSET_X, TOOL_1_Y - MIDDLE_OFFSET_Y - 2*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - MIDDLE_OFFSET_X, TOOL_1_Y - MIDDLE_OFFSET_Y - 3*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - 2*MIDDLE_OFFSET_X, TOOL_1_Y, TOOL_1_Z ),
  ( TOOL_1_X - 2*MIDDLE_OFFSET_X, TOOL_1_Y - TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - 2*MIDDLE_OFFSET_X, TOOL_1_Y - 2*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - 2*MIDDLE_OFFSET_X, TOOL_1_Y - 3*TOOL_DIST, TOOL_1_Z ),
  ( TOOL_1_X - 2*MIDDLE_OFFSET_X, TOOL_1_Y - 4*TOOL_DIST, TOOL_1_Z )
]

def get_tool_slot_position(num):
  return TOOL_POSITIONS[num-1]

# Return the tool number of the slot that the spindle is currently 
# located in. Returns None if the the spindle is not in a tool slot
# location. Used as a safety check when swapping tools.
def get_tool_slot_num(x,y,z):
  for (i,slot) in enumerate(TOOL_POSITIONS):
    if(
      abs(x-slot[0]) < EPS and
      abs(y-slot[1]) < EPS and
      abs(z-slot[2]) < EPS 
    ):
      return i+1
  return None


def is_over_tool_slot_num(x,y,num):
  if( num < len(TOOL_POSITIONS) and num >= 1 ):
    slot = TOOL_POSITIONS[num-1]
    if(
      abs(x-slot[0]) < EPS and
      abs(y-slot[1]) < EPS
    ):
      return True
  return False

def is_over_tool_slot(x,y):
  for slot in TOOL_POSITIONS:
    if(
      abs(x-slot[0]) < EPS and
      abs(y-slot[1]) < EPS
    ):
      return True

  return False
