print("in metrology __init__.py")
import numpy
from enum import Enum
import metrology.leastSquaresCircle
import metrology.leastSquaresSphere
import metrology.helpers
import skg

from importlib import reload
reload(metrology.leastSquaresSphere)

_DEBUG = True

def setDebug(d):
  global _DEBUG
  _DEBUG = d

def bestFitSphere(pts):
  transpose = pts.T
  return metrology.leastSquaresSphere.sphereFit(transpose[0], transpose[1], transpose[2])

# Calculates a best fit circle in 3D
# * First calculates best fit plane
# * Projects points onto plane
# * Calculates best fit 2d circle using arbitrary basis vectors on the plane
# * Return center point in origin space with circle radius and plane normal
def bestFitCircle(pts):
  plane = bestFitPlane(pts)

  planeOrigin = plane[0]
  planeN = plane[1]
  up = [ 1, 0, 0 ]
  if abs(abs(numpy.dot(up, planeN))-1) < .0001:
    up = [ 0, 1, 0 ]

  xvec = numpy.cross(planeN, up)
  xvec = xvec / numpy.linalg.norm(xvec)

  yvec = numpy.cross(planeN, xvec)

  planePts = []
  for p in pts:
    planePt = numpy.subtract(projectPointOntoPlane(p, plane), planeOrigin)
    x = numpy.dot(planePt, xvec)
    y = numpy.dot(planePt, yvec)

#    print("Projected to plane: ", planePt, x, y)
    print(x, y)
    
    planePts.append([ x, y, 0 ])

  circle = skg.nsphere.nsphere_fit(planePts)
  circle2d = (circle[1], circle[0])

  print("Circle2D", circle2d)
  print("xvec", xvec)
  print("yvec", yvec)
  print("planeOrigin", planeOrigin)
  print("numpy.multiply(circle2d[0][0], xvec)", numpy.multiply(circle2d[0][0], xvec))
  print("numpy.multiply(circle2d[0][1], yvec)", numpy.multiply(circle2d[0][1], yvec))

  center = numpy.multiply(circle2d[0][0], xvec)+numpy.multiply(circle2d[0][1], yvec)+planeOrigin

  return (center, circle2d[1], planeN)

def bestFitPlane(pts):
  pts_array = numpy.array(pts)
  mean = numpy.mean(pts_array, axis=0)
  svd = numpy.linalg.svd((pts_array-mean).T)

  # return tuple with (pt on plane, normal of plane)
  return (mean, svd[0].T[2])

def bestFitLine(pts):
  pts_array = numpy.array(pts)
  mean = numpy.mean(pts_array, axis=0)
  svd = numpy.linalg.svd(pts_array-mean)

  if _DEBUG:
    print("SVD", svd)

  # return tuple with (pt on line, direction of line)
  return (mean, svd[2][0])

def projectPointOntoPlane(point, plane):
  planePt = plane[0]
  planeN = plane[1]

  vec = numpy.subtract(point, planePt)
  
  return numpy.subtract(point, numpy.multiply(planeN, numpy.dot(vec, planeN))) 

class Feature:
  def __init__(self):
    self._featureTransform = None

    self._points = numpy.array([])
    self._average = None
    self._circle2D = None
    self._sphere = None
    self._line = None
    self._plane = None
    self._circle = None

  def setTransformWithAxisAngle(self, axis, angle):
    self._featureTransform = metrology.helpers.makeRotationAxis(axis, angle)
    self.makeDirty()

  def makeDirty(self):
    """Clears any cached calculations, such as average position, best fit circle, etc."""
    self._average = None
    self._circle2D = None
    self._sphere = None
    self._line = None
    self._plane = None
    self._circle = None
    self._transformedPoints = None

  def addPoint(self, x, y, z):
    if len(self._points) == 0:
      self._points = numpy.append(self._points, numpy.array([x,y,z])).reshape(1,3)
      self._points.setflags(write=False)
    else:
      self._points = numpy.append(self._points, numpy.array([[x,y,z]]), axis=0)
      self._points.setflags(write=False)
    self.makeDirty()

    if _DEBUG:
      print("Points: ")
      for p in self._points:
        print("%s\t%s\t%s" % ( p[0], p[1], p[2] ))

  def clearPoints(self):
    self._points = numpy.array([])
    self.makeDirty()

    if _DEBUG:
      print("Cleared points!")

  def points(self):
    if self._transformedPoints is None:
      if self._featureTransform is None:
        self._transformedPoints = numpy.array(self._points)
        self._transformedPoints.setflags(write=False)
      else:
        transformed = [ self._featureTransform @ [ p[0], p[1], p[2], 1 ] for p in self._points ]
        self._transformedPoints = numpy.array([ (p[0],p[1],p[2]) for p in transformed ])
        self._transformedPoints.setflags(write=False)

    return self._transformedPoints

  def average(self):
    if self._average is None:
      self._average = self.points().mean(axis=0)

    if _DEBUG:
      print("Average: ", self._average)

    return self._average

  def plane(self):
    if self._plane is None:
      self._plane = bestFitPlane(self.points())

    return self._plane

  def line(self):
    if self._line is None:
      self._line = bestFitLine(self.points())

    if _DEBUG:
      print("Line: ", self._line)

    return self._line

  def sphere(self):
    if self._sphere is None:
      self._sphere = skg.nsphere.nsphere_fit(self.points())
      self._debugSphere = bestFitSphere(self.points())

    if _DEBUG:
      print("Sphere: ", self._sphere)
      print("Least Squares Sphere: ", self._debugSphere)

    return self._sphere

  def circle(self):
    if self._circle is None:
      self._circle = metrology.bestFitCircle(self.points())

    if _DEBUG:
      print("Circle: ", self._circle)

    return self._circle

  def circle2D(self):
    if self._circle2D is None:
      ptData = self.points().T
      pts = numpy.array([ ptData[0],ptData[1] ]).T
      circle = skg.nsphere.nsphere_fit(pts)
      self._circle2D = (circle[1], circle[0])

    if _DEBUG:
      print("Circle2D: ", self._circle2D)

    return self._circle2D

featureManagerInstance = None

class FeatureSet:
  def __init__(self):
    self.features = {}
    self.activeFeatureID = 0

  def setActiveFeatureID(self, id):
    self.activeFeatureID = int(id)

  def getActiveFeatureID(self):
    return self.activeFeatureID

  def getFeature(self, id):
    feature = self.features.get(id, None)
    if feature == None:
      feature = Feature()
      self.features[id] = feature

    return feature

  def getActiveFeature(self):
    return self.getFeature(self.activeFeatureID)

class FeatureManager:
  def __init__(self):
    self.sets = [ FeatureSet() ];

  def push(self):
    self.sets.append( FeatureSet() )

  def pop(self):
    self.sets.pop()

  def getActiveFeatureSet(self):
    return self.sets[-1]

  def getInstance():
    global featureManagerInstance
    if featureManagerInstance == None:
      featureManagerInstance = FeatureManager()

    return featureManagerInstance
