import math
import bisect
import os
import numpy as np
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_instance = None

class ProbeCalibration():
  def __init__(self, directory="/var/opt/pocketnc/", filename="probe-calibration"):
    self._directory = directory
    self._filename = filename
    self._enabled = True
    self._calibration = None
    self._probeDiameter = 0
    self._approximateTouchPoint = False

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
    actualR = (actualDiameter+probeTipDiameter)*.5

    sphere = feature.sphere()
    data = np.array(feature.points())

    data = data-np.array([ sphere[1][0], sphere[1][1], sphere[1][2] ])

    probeCalibration = []

    idealX = 0
    idealY = 0
    idealZ = actualR

    x = data[0][0]
    y = data[0][1]
    z = data[0][2]

    mag = actualR-math.sqrt(x*x+y*y+z*z)
    probeCalibration.append([ 0, [[ 0, mag ], [ 360, mag ]] ])

    i = 1
    for ringIndex in range(1,rings+1):
      latAngle = math.radians(90 / rings * ringIndex)

      latArray = []
      for pointIndex in range(samplesPerRing):
        longAngle = math.radians(360 / samplesPerRing * pointIndex)

        idealX = actualR * math.sin(latAngle) * math.cos(longAngle)
        idealY = actualR * math.sin(latAngle) * math.sin(longAngle)
        idealZ = actualR * math.cos(latAngle)

        x = data[i][0]
        y = data[i][1]
        z = data[i][2]

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
    # x, y, z are a normalized direction that the probe is traveling in
    logger.debug("in setProbeDirection (%s, %s, %s)" % (x, y, z))
    self._dirx = x
    self._diry = y
    self._dirz = z

    self._compensation = self.computeCompensation(-x, -y, -z)

  def getCompensation(self):
    if self._enabled:
      return self._compensation

    return (0,0,0)

  def computeCompensation(self, x, y, z):
    if self._calibration:
      # x, y, z is a normalized direction that represents the normal of the surface
      # that we're approaching
      logger.debug("computing compensation for direction (%s, %s, %s)" % (x,y,z))

      latAngle = math.degrees(math.acos(z))
      longAngle = math.degrees(math.atan2(y,x))
      if longAngle < 0:
        longAngle += 360

      latIndex = bisect.bisect_left([ elem[0] for elem in self._calibration ], latAngle)

      if latIndex == 0:
        latIndex = 1

      logger.debug("latIndex: %s" % (latIndex,))

      latIndex = min(len(self._calibration)-1, latIndex)
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

      logger.debug("t0: %s" % (t0, ))
      logger.debug("t1: %s" % (t1, ))
      logger.debug("latT: %s" % (latT, ))

      compMag0 = compMag0_0*(1-t0) + compMag0_1*t0
      compMag1 = compMag1_0*(1-t1) + compMag1_1*t1

      compMag = compMag0*(1-latT)+compMag1*latT

      comp = ( 
        compMag*x,
        compMag*y,
        compMag*z
      )

      logger.debug("Computed compensation for direction (%s, %s, %s): (%s, %s, %s)" % (x,y,z,comp[0],comp[1],comp[2]))

      return comp
    return (0,0,0)

  def enableApproximateTouchPoint(self, probeDiameter):
    self._approximateTouchPoint = True
    self._probeDiameter = probeDiameter

  def disableApproximateTouchPoint(self):
    self._approximateTouchPoint = False
    self._probeDiameter = probeDiameter

def getInstance():
  global _instance
  if _instance is None:
    _instance = ProbeCalibration()

  return _instance


