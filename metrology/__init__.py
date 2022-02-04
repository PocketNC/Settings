import numpy
from enum import Enum
import metrology.leastSquaresCircle

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

  print("SVD", svd)

  # return tuple with (pt on line, direction of line)
  return (mean, svd[2][0])

class Feature:
  def __init__(self):
    self._points = numpy.array([])
    self._average = None
    self._center2D = None
    self._line = None

  def makeDirty(self):
    """Clears any cached calculations, such as average position, best fit circle, etc."""
    self._average = None
    self._circle2D = None
    self._line = None
    self._plane = None

  def addPoint(self, x, y, z):
    if len(self._points) == 0:
      self._points = numpy.append(self._points, numpy.array([x,y,z])).reshape(1,3)
    else:
      self._points = numpy.append(self._points, numpy.array([[x,y,z]]), axis=0)
    self.makeDirty()

    print("Points: ", self._points)

  def clearPoints(self):
    self._points = numpy.array([])
    self.makeDirty()

    print("Cleared points!")

  def points(self):
    return self._points

  def average(self):
    if self._average == None:
      self._average = self._points.mean(axis=0)

    print("Average: ", self._average)

    return self._average

  def plane(self):
    if self._plane == None:
      self._plane = bestFitPlane(self._points)

    return self._plane

  def line(self):
    if self._line == None:
      self._line = bestFitLine(self._points)

    print("Line: ", self._line)

    return self._line

  def circle2D(self):
    if self._circle2D == None:
      self._circle2D = metrology.leastSquaresCircle.calculate(self._points)

    print("Circle2D: ", self._circle2D)

    return self._circle2D

featureManagerInstance = None

class FeatureManager:
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

  def getInstance():
    global featureManagerInstance
    if featureManagerInstance == None:
      featureManagerInstance = FeatureManager()

    return featureManagerInstance
