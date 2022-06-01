import math
import bisect
import os
import numpy as np
import json
from datetime import datetime

_instance = None

class ProbeCalibration():
  def __init__(self, directory="/var/opt/pocketnc/", filename="probe-calibration"):
    self._directory = directory
    self._filename = filename
    self._enabled = True
    self._calibration = None

    path = os.path.join(directory, filename)

    try:
      if os.path.exists(path):
        with open(path) as file:
          data = file.read()
          self._calibration = json.loads(data)
    except:
      raise ValueError("Failed to parse probe calibration data.")

    self.setProbeDirection(0,0,0)

  def disableCompensation(self):
    self._enabled = False

  def enableCompensation(self):
    self._enabled = True

  # Sphere feature must have points collected in the same way as add-points-probe-sphere
  def setProbeCalibration(self, actualDiameter, probeTipDiameter, feature, rings, samplesPerRing, theta):
    actualR = (actualDiameter-probeTipDiameter)*.5

    sphere = feature.sphere()
    data = np.array(feature.points())

    data = data-np.array([ sphere[1][0], sphere[1][1], sphere[1][2] ])

    probeCalibration = []

    idealX = 0
    idealY = 0
    idealZ = actualR

    x = pts[0][0]
    y = pts[0][1]
    z = pts[0][2]

    mag = actualR-math.sqrt(x*x+y*y+z*z)
    probeCalibration.append([ 0, [ 0, mag ], [ 360, mag ] ])

    for ringIndex in range(1,rings+1):
      latAngle = math.radians(90 / rings * ringIndex)

      latArray = []
      for pointIndex in range(samplesPerRing):
        longAngle = math.radians(360 / samplesPerRing * pointIndex)

        idealX = actualR * math.sin(latAngle) * math.cos(longAngle)
        idealY = actualR * math.sin(latAngle) * math.sin(longAngle)
        idealZ = actualR * math.cos(latAngle)

        x = pts[i][0]
        y = pts[i][1]
        z = pts[i][2]

        mag = actualR-math.sqrt(x*x+y*y+z*z)

        latArray.append([ math.degrees(longAngle), mag ])
        i += 1

      latArray.append([ latArray[0][0]+360, latArray[0][1] ])

      probeCalibration.append([ math.degrees(latAngle), latArray ])

    self._calibration = probeCalibration

    
  # TODO - Save probe compensation to specific probe number.
  #      - Currently only saves to file with date and time and a symlink is created
  #      - to a specific name. This allows us to always open a specific file at start up,
  #      - without worrying about overwriting previous data (the symlink could feasibly be
  #      - reverted to an older one).
  def saveProbeCalibration(self):
    path = os.path.join(self._directory, self._filename)
    pathDateTime = os.path.join(self._directory, self._filename + "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    with open(pathDateTime, 'w') as file:
      file.write(json.dumps(self._calibration))

    os.unlink(path)
    os.symlink(pathDateTime, path)

  def setProbeDirection(self, x, y, z):
    print("in setProbeDirection (%s, %s, %s)" % (x, y, z))
    self._dirx = x
    self._diry = y
    self._dirz = z

    self._compensation = self.computeCompensation(-x, -y, -z)

  def getCompensationX(self):
    if self._enabled:
      return self._compensation[0]

    return 0

  def getCompensationY(self):
    if self._enabled:
      return self._compensation[1]

    return 0

  def getCompensationZ(self):
    if self._enabled:
      return self._compensation[2]

    return 0

  def computeCompensation(self, x, y, z):
    print("computing compensation for direction (%s, %s, %s)" % (x,y,z))

    latAngle = math.degrees(math.acos(z))
    longAngle = math.degrees(math.atan2(y,x))
    if longAngle < 0:
      longAngle += 360

    latIndex = bisect.bisect_left([ elem[0] for elem in self._calibration ], latAngle)

    if latIndex == 0:
      latIndex = 1

    print("latIndex: %s" % (latIndex,))

    latArray0 = self._calibration[latIndex-1]
    latArray1 = self._calibration[latIndex]

    latAngle0 = latArray0[0]
    latAngle1 = latArray1[0]

    longIndex0 = bisect.bisect_left([ elem[0] for elem in latArray0[1] ], longAngle)
    longIndex1 = bisect.bisect_left([ elem[0] for elem in latArray1[1] ], longAngle)

    compMag0_0 = latArray0[1][longIndex0-1][1]
    compMag0_1 = latArray0[1][longIndex0][1]

    longAngle0_0 = latArray0[1][longIndex0-1][0]
    longAngle0_1 = latArray0[1][longIndex0][0]

    compMag1_0 = latArray1[1][longIndex1-1][1]
    compMag1_1 = latArray1[1][longIndex1][1]

    longAngle1_0 = latArray1[1][longIndex1-1][0]
    longAngle1_1 = latArray1[1][longIndex1][0]

    t0 = (longAngle-longAngle0_0)/(longAngle0_1-longAngle0_0)
    t1 = (longAngle-longAngle1_0)/(longAngle1_1-longAngle1_0)

    latT = (latAngle-latAngle0)/(latAngle1-latAngle0)

    print("t0: %s" % (t0, ))
    print("t1: %s" % (t1, ))
    print("latT: %s" % (latT, ))

    compMag0 = compMag0_0*(1-t0) + compMag0_1*t0
    compMag1 = compMag1_0*(1-t1) + compMag1_1*t1

    compMag = compMag0*(1-latT)+compMag1*latT

    comp = [ 
      compMag*x,
      compMag*y,
      compMag*z
    ]

    print("Computed compensation for direction (%s, %s, %s): (%s, %s, %s)" % (x,y,z,comp[0],comp[1],comp[2]))

    return comp

def getInstance():
  global _instance
  if _instance is None:
    _instance = ProbeCalibration()

  return _instance


