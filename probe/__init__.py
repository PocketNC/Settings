import math
import bisect
import os
import numpy as np
from datetime import datetime

_instance = None

class ProbeCalibration():
  def __init__(self, directory="/var/opt/pocketnc/", filename="probe-calibration-xy"):
    self._directory = directory
    self._filename = filename
    self._enabled = True
    self.theta_values = []
    self.r_values = []

    path = os.path.join(directory, filename)

    try:
      if os.path.exists(path):
        with open(path) as file:
          data = file.read().split("\n")
          for line in data:
            line_data = line.split()

            if len(line_data) > 0:
              if len(line_data) != 2:
                raise ValueError("Line has %s values, expecting 2." % len(line_data))
              else:
                self.theta_values.append(float(line_data[0]))
                self.r_values.append(float(line_data[1]))
      else:
        self.theta_values = [ 0, 2*math.pi ]
        self.r_values = [ 0, 0 ]
    except:
      raise ValueError("Failed to parse probe xy calibration data.")

    if self.theta_values[0] > 0 or self.theta_values[-1] < 2*math.pi-.000001:
      raise ValueError("Probe calibration data doesn't cover full range of values")

    self.setProbeDirection(0,0,0)

  def disableCompensation(self):
    self._enabled = False

  def enableCompensation(self):
    self._enabled = True

  def setProbeCompensationCircle2D(self, actualDiameter, probeTipDiameter, feature):
    actualR = (actualDiameter-probeTipDiameter)*.5

    circle = feature.circle2D()
    data = np.array(feature.points())

    data = data-np.array([ circle[0][0], circle[0][1], 0 ])

    pts = []
    for pt in data:
      theta = math.atan2(pt[1], pt[0])

      if theta < 0:
        theta += 2*math.pi

      r = math.sqrt(pt[0]*pt[0]+pt[1]*pt[1])
      pts.append([ theta, r-actualR ])

    pts.sort(key=lambda a: a[0])
    first = pts[0]
    last = pts[-1]

    pts.insert(0, [ last[0]-math.pi*2, last[1] ])
    pts.append([ first[0]+math.pi*2, first[1] ])

    self.theta_values = []
    self.r_values = []
    for pt in pts:
      self.theta_values.append(pt[0])
      self.r_values.append(pt[1])

    
  # TODO - Save probe compensation to specific probe number.
  #      - Currently only saves to file with date and time and a symlink is created
  #      - to a specific name. This allows us to always open a specific file at start up,
  #      - without worrying about overwriting previous data (the symlink could feasibly be
  #      - reverted to an older one).
  def saveProbeCompensation(self):
    path = os.path.join(self._directory, self._filename)
    pathDateTime = os.path.join(self._directory, self._filename + "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

    with open(pathDateTime, 'w') as file:
      for i in range(len(self.theta_values)):
        file.write("%s\t%s\n" % (self.theta_values[i], self.r_values[i]))

    os.unlink(path)
    os.symlink(pathDateTime, path)


  def setProbeDirection(self, x, y, z):
    self._dirx = x
    self._diry = y
    self._dirz = z

    self._compensation = self.computeCompensation(x, y, z)

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
    # TODO - include z in the calculations, for now we only look at the xy direction
    if abs(x) < .00001 and abs(y) < .00001:
      return [0, 0, 0]

    theta = math.atan2(y, x)
    if theta < 0:
      theta += 2*math.pi

    index = bisect.bisect_left(self.theta_values, theta)

    print("index: %s" % (index,))

    theta0 = self.theta_values[index-1]
    theta1 = self.theta_values[index]

    print("theta0, theta1: (%s, %s)" % (theta0, theta1))

    r0 = self.r_values[index-1]
    r1 = self.r_values[index]

    print("r0, r1: (%s, %s)" % (r0, r1))

    print("theta: %s" % (theta,))

    t = (theta-theta0)/(theta1-theta0)

    print("t: %s" % (t, ))

    r = r0*(1-t)+r1*t

    comp = [ r*math.cos(theta), r*math.sin(theta), 0 ]

    print("Computed compensation for direction (%s, %s, %s): (%s, %s, %s)" % (x,y,z,comp[0],comp[1],comp[2]))

    return comp


def getInstance():
  global _instance
  if _instance is None:
    _instance = ProbeCalibration()

  return _instance


