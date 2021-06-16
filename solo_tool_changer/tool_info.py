import math

# these are taken from and must match the tool change G code subroutines
TOOL_1_X = 6.2093
TOOL_1_Y = 2.9180
TOOL_1_Z = -6.2277
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

def is_over_tool_slot(x,y):
  for slot in TOOL_POSITIONS:
    if(
      abs(x-slot[0]) < EPS and
      abs(y-slot[1]) < EPS
    ):
      return True

  return False
