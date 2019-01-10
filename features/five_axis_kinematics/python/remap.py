from stdglue import *

import math
import subprocess
from interpreter import INTERP_OK

current_five_axis_kinematics = False

# tool length offset MUST be on for five axis kinematics to work
# i.e. to enable five axis kinematics:
# G43 H2
# G60

# to disable five axis kinematics:
# G60.1
# You can now disable tool length offset with a G49
# or issue commands such as G53 Z0 to ignore tool length offset

class FiveAxisKinematics:
  def forward(self, pos):
    (x,y,z,a,b) = pos

    A = math.radians(a)
    B = math.radians(b)

    CA = math.cos(A)
    CB = math.cos(B)

    SA = math.sin(A)
    SB = math.sin(B)

    qx = x*CB+y*SB*SA-z*SB*CA
    qy = y*CA+z*SA
    qz = x*SB-y*CB*SA+z*CB*CA

    return (qx, qy, qz, a ,b)

  def inverse(self, pos):
    (x,y,z,a,b) = pos

    A = math.radians(a)
    B = math.radians(b)

    CA = math.cos(A)
    CB = math.cos(B)

    SA = math.sin(A)
    SB = math.sin(B)

    px = x*CB+z*SB
    py = x*SB*SA+y*CA-z*CB*SA
    pz = -x*SB*CA+y*SA+z*CB*CA

    return (px, py, pz, a ,b)

def five_axis_kinematics_on(self, **words):
  global current_five_axis_kinematics

  try:
    self.execute("M141");

    if not current_five_axis_kinematics:

      # x,y,z are trivial kinematics coordinates
      x = self.current_x
      y = self.current_y
      z = self.current_z

      a = self.AA_current
      b = self.BB_current

      print "\n\nturning on five axis kinematics"

      kins = FiveAxisKinematics()

      Q = kins.forward((x,y,z,a,b))

      print Q

      self.execute("G0 X%.4f Y%.4f Z%.4f\n" % (Q[0], Q[1], Q[2]))

      current_five_axis_kinematics = True


  except InterpreterException,e:
    msg = "%d: '%s' - %s" % (e.line_number, e.line_text, e.error_message)
    return msg
  return INTERP_OK

def five_axis_kinematics_off(self, **words):
  global current_five_axis_kinematics

  try:
    self.execute("M140");

    if current_five_axis_kinematics:

      # x,y,z are local work piece coordinates
      x = self.current_x
      y = self.current_y
      z = self.current_z

      a = self.AA_current
      b = self.BB_current

      print "\n\nturning off five axis kinematics"

      kins = FiveAxisKinematics()

      print "before ", (x,y,z,a,b)

      P = kins.inverse((x,y,z,a,b))

      self.execute("G0 X%.4f Y%.4f Z%.4f\n" % (P[0], P[1], P[2]))

      print P

      current_five_axis_kinematics = False

  except InterpreterException,e:
    msg = "%d: '%s' - %s" % (e.line_number, e.line_text, e.error_message)
    return msg
  return INTERP_OK
