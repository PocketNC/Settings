"""
Metrology package for calculating best fit features from sets of points. The most
useful class is `Feature`. A `Feature` object is a set of
points, which has methods such as `Feature.line`, `Feature.plane`, or `Feature.sphere`
for returning information that defines those types of features based on the points added to the
`Feature`. 

There is also a `FeatureManager` class and `FeatureMap` class intended to
be used by `oword`s and `namedparams` for easier interactions with Features from a G code context where
the only data type is floating point numbers.

This package, coupled with `oword`s, `namedparams` and a probing interface that allows
users to plan out probing routines will provide a powerful way of inspecting parts
made on Penta machines.

This package is also used in combination with a Mitutyo CMM + Renishaw UCC Server
to calibrate Penta machines internally.

Copyright Penta Machine Company 2023
"""
import numpy as np
from enum import Enum
import scipy.optimize
import metrology.leastSquaresSphere
import metrology.helpers
import skg
import math
import logging
import json

logger = logging.getLogger(__name__)

class FeatureEncoder(json.JSONEncoder):
  """
  A JSON encoder that turns Feature objects into a dictionary that is readily identifiable as a Feature object, so 
  when the JSON is decoded in Python it can automatically turn those objects into Feature objects.
  """

  def default(self, o):
    if isinstance(o, Feature):
      return o.toJSON()

    return super().default(o)

_DEBUG = False

def setDebug(d):
  global _DEBUG
  _DEBUG = d

'''
Following two methods (unit_vector and angle_between) adapted from:
https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
'''
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in degrees between vectors 'v1' and 'v2'::
            >>> angle_between((1, 0, 0), (0, 1, 0))
            180/pi * 1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            180/pi * 0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            180/pi * 3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return (180/math.pi)*np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def angle_between_ccw_2d(v1,v2):
  logger.debug('angle_between_ccw_2d %s %s' % (v1, v2))
  dot = v1[0] * v2[0] + v1[1] * v2[1]
  det = v1[0] * v2[1] - v1[1] * v2[0]
  return math.atan2(det,dot) * 180/math.pi

def line_plane_intersect(dir_line, pt_line, dir_plane, pt_plane):
  dir_line = np.array(dir_line)
  pt_line = np.array(pt_line)
  dir_plane = np.array(dir_plane)
  pt_plane = np.array(pt_plane)

  norm_dot_vec = np.dot(dir_plane, dir_line)
  if( abs(norm_dot_vec) < .00001):
    return None

  w = pt_line - pt_plane
  si = -np.dot(dir_plane, w) / norm_dot_vec
  pos_intersect = w + si * dir_line + pt_plane
  return pos_intersect

def line_intersection_2d(p1,v1,p2,v2):
  v1 = np.array(v1[0:2])
  v2 = np.array(v2[0:2])
  p1 = np.array(p1[0:2])
  p2 = np.array(p2[0:2])

  v12 = p1 - p2
  v1_perp = np.array([-v1[1], v1[0]])
  denom = np.dot(v1_perp, v2)
  num = np.dot(v1_perp, v12)
  return (num / denom.astype(float))*v2 + p2


def diff(v1,v2):
  return [ v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2] ]

def dot(v1,v2):
  return v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2]

def nearestPointOnLine(pt, line):
  dx = pt[0]-line[0][0]
  dy = pt[1]-line[0][1]
  dz = pt[2]-line[0][2]

  dot = dx*line[1][0] + dy*line[1][1] + dz*line[1][2]

  return (line[0][0]+dot*line[1][0], line[0][1]+dot*line[1][1], line[0][2]+dot*line[1][2])

# with help from https://nvlpubs.nist.gov/nistpubs/jres/103/6/j36sha.pdf
def bestFitCylinder(pts, pt=None, axis=[ 0,0, 1], radius=1):
  data = pts.T

  x = data[0]
  y = data[1]
  z = data[2]

  def distFromCylinder(c):
    ptX = c[0]
    ptY = c[1]
    ptZ = c[2]

    dirX = c[3]
    dirY = c[4]
    dirZ = c[5]

    dirMag = math.sqrt(dirX*dirX+dirY*dirY+dirZ*dirZ)
    dirX = dirX/dirMag
    dirY = dirY/dirMag
    dirZ = dirZ/dirMag

    r = c[6]

    # (u,v,w) is the cross product of the direction vector (dirX, dirY, dirZ) 
    # with the vector from each point P to a known point on the line (ptX, ptY, ptZ)
    # The magnitude of the resulting vector is the distance from the point to the line defined by the direction, dir, and point, pt.
    # Note that u, v and w are numpy arrays with each element representing a single (x,y,z) point P.
    u = dirZ*(y - ptY) - dirY*(z - ptZ)
    v = dirX*(z - ptZ) - dirZ*(x - ptX)
    w = dirY*(x - ptX) - dirX*(y - ptY)

    # So what we're returning here is a numpy array of distances from our cylinder.
    # When we minimize this value, we'll have our pt, dir and radius for a best fit cylinder
    return np.sqrt(u*u + v*v + w*w) - r

# Using the Jacobian matrix can result in fewer iterations of the least squares solver
# But this doesn't always seem to give the correct answer.
  def jac(c):
    ptX = c[0]
    ptY = c[1]
    ptZ = c[2]

    dirX = c[3]
    dirY = c[4]
    dirZ = c[5]

    dirMag = math.sqrt(dirX*dirX+dirY*dirY+dirZ*dirZ)
    dirX = dirX/dirMag
    dirY = dirY/dirMag
    dirZ = dirZ/dirMag

    u = dirZ*(y - ptY) - dirY*(z - ptZ)
    v = dirX*(z - ptZ) - dirZ*(x - ptX)
    w = dirY*(x - ptX) - dirX*(y - ptY)

    d = np.sqrt(u*u + v*v + w*w)

    ddPtX = (v*dirZ - w*dirY)/d
    ddPtY = (-u*dirZ + w*dirX)/d
    ddPtZ = (u*dirY + v*dirZ)/d
    ddDirX = (v*(z - ptZ) + w*(-y+ptY))*(1-dirX*dirX)/dirMag/d
    ddDirY = (u*(-z+ptZ) + w*(x-ptX))*(1-dirY*dirY)/dirMag/d
    ddDirZ = (u*(y-ptY) + v*(-x+ptX))*(1-dirZ*dirZ)/dirMag/d
    ddR = np.full((x.size,), -1)

    return np.column_stack((ddPtX, ddPtY, ddPtZ, ddDirX, ddDirY, ddDirZ, ddR))
    
  (cylinder, ier) = scipy.optimize.leastsq(distFromCylinder, np.array([ pt[0] if pt is not None else x.mean(), pt[1] if pt is not None else y.mean(), pt[2] if pt is not None else z.mean(), axis[0], axis[1], axis[2], radius ]))

  (ptX, ptY, ptZ, dirX, dirY, dirZ, r) = cylinder

  dirMag = math.sqrt(dirX*dirX+dirY*dirY+dirZ*dirZ)

  return ((ptX, ptY, ptZ), (dirX/dirMag, dirY/dirMag, dirZ/dirMag), r)

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
  if abs(abs(np.dot(up, planeN))-1) < .0001:
    up = [ 0, 1, 0 ]

  xvec = np.cross(planeN, up)
  xvec = xvec / np.linalg.norm(xvec)

  yvec = np.cross(planeN, xvec)

  planePts = []
  for p in pts:
    planePt = np.subtract(projectPointToPlane(p, plane), planeOrigin)
    x = np.dot(planePt, xvec)
    y = np.dot(planePt, yvec)

    planePts.append([ x, y, 0 ])

  circle = skg.nsphere.nsphere_fit(planePts)
  circle2d = (circle[1], circle[0])

  if _DEBUG:
    logger.debug("Circle2D %s", circle2d)
    logger.debug("xvec %s", xvec)
    logger.debug("yvec %s", yvec)
    logger.debug("planeOrigin %s", planeOrigin)
    logger.debug("np.multiply(circle2d[0][0], xvec) %s, %s", np.multiply(circle2d[0][0], xvec))
    logger.debug("np.multiply(circle2d[0][1], yvec) %s, %s", np.multiply(circle2d[0][1], yvec))

  center = np.multiply(circle2d[0][0], xvec)+np.multiply(circle2d[0][1], yvec)+planeOrigin

  return (circle2d[1], center, planeN)

def bestFitPlane(pts):
  pts_array = np.array(pts)
  mean = np.mean(pts_array, axis=0)
  svd = np.linalg.svd((pts_array-mean).T)

  # return tuple with (pt on plane, normal of plane)
  return (mean, svd[0].T[2])

def bestFitLine(pts):
  pts_array = np.array(pts)
  mean = np.mean(pts_array, axis=0)
  svd = np.linalg.svd(pts_array-mean)
  dir = svd[2][0]

  if _DEBUG:
    logger.debug("SVD %s", svd)

  # The direction isn't guaranteed to be related to the direction the points
  # were gathered in. Check that the direction from the first to last point
  # is roughly in the same direction as the direction of the line. If the line
  # direction is pointed roughly in the opposite direction, flip the direction.
  # Either way, it defines the same line, but this makes the direction of the
  # line more deterministic, so users can make assumptions about the direction
  # of the line based on the order the points were gathered in.
  approx_dir = pts_array[-1]-pts_array[0]
  approx_dir *= 1.0/np.linalg.norm(approx_dir)
  if np.dot(approx_dir, dir) < 0:
    dir *= -1

  # return tuple with (pt on line, direction of line)
  return (mean, dir)

def projectPointToPlane(point, plane):
  planePt = plane[0]
  planeN = plane[1]

  vec = np.subtract(point, planePt)
  
  return np.subtract(point, np.multiply(planeN, np.dot(vec, planeN))) 

def projectDirectionToPlane(direction, plane):
  planePt = plane[0]
  planeN = plane[1]

  return np.subtract(direction, np.multiply(planeN, np.dot(direction, planeN))) 

def projectLineToPlane(line, plane):
  pt = projectPointToPlane(line[0], plane)
  dir = projectDirectionToPlane(line[1], plane)

  mag = math.sqrt(dir[0]*dir[0]+dir[1]*dir[1]+dir[2]*dir[2])
  return (pt, (dir[0]/mag, dir[1]/mag, dir[2]/mag))

def intersectLines(line1, line2):
  p1 = line1[0]
  d1 = line1[1]

  p2 = line2[0]
  d2 = line2[1]

  p2_dot_d1 = dot(p2, d1)
  p1_dot_d1 = dot(p1, d1)

  p2_dot_d2 = dot(p2, d2)
  p1_dot_d2 = dot(p1, d2)

  d1_dot_d1 = dot(d1, d1)
  d1_dot_d2 = dot(d1, d2)
  d2_dot_d2 = dot(d2, d2)

  den = 1 - (d1_dot_d2)*(d1_dot_d2)/(d2_dot_d2*d1_dot_d1)
  
  if abs(den) < 0.000001:
    t1 = 0
  else:
    t1 = ((p2_dot_d1-p1_dot_d1)/(d1_dot_d1) + (p1_dot_d2*d1_dot_d2 - p2_dot_d2*d1_dot_d2)/(d2_dot_d2*d1_dot_d1))/den

  t2 = (p1_dot_d2 + t1*d1_dot_d2 - p2_dot_d2)/d2_dot_d2

  A = (p1[0]+d1[0]*t1,p1[1]+d1[1]*t1,p1[2]+d1[2]*t1)
  B = (p2[0]+d2[0]*t2,p2[1]+d2[1]*t2,p2[2]+d2[2]*t2)

  return (A,B)

def convertJSONDataToFeatures(data):
  if Feature.isJSONObjectAFeature(data):
    return Feature(data)

  if type(data) == list:
    d = []
    for obj in data:
      d.append(convertJSONDataToFeatures(obj))
    return d
  elif type(data) == dict:
    d = {}
    for (k,v) in data.items():
      d[k] = convertJSONDataToFeatures(v)
    return d

  return data

class Feature:
  """
  A Feature object represents a set of points. Methods include a number
  of best fit primitives. Most methods cache the result of any calculations
  performed on the points. In a G code context, where only a single floating
  point value can be returned at a time, this helps to avoid unnecessary
  recalculations when calling it multiple times in succession to get the X, Y and Z
  components of a point or direction vector.
  """
  def isJSONObjectAFeature(data):
    """Returns True if a dict object has the "isFeature" key. This is used by
    `convertJSONDataToFeatures` to automatically convert a deserialized JSON
    data structure to Feature objects."""
    return type(data) == dict and data.get("isFeature", False)

  def toJSON(self):
    """Convert this `Feature` object to dict, suitable for being serialized to JSON."""
    obj = {
      "isFeature": True,
      "points": self._points.tolist()
    }
    
    if self._featureTransform:
      obj["transform"] = self._featureTransform.tolist()

    return obj

  def _initFromJSON(self, data):
    t = data.get("transform", None)
    self._featureTransform = np.array(t) if t else None
    self._points = np.array(data["points"])

  def _initFromList(self, data):
    self._featureTransform = None
    self._points = np.array(data)

  def __init__(self, data=[]):
    if Feature.isJSONObjectAFeature(data):
      self._initFromJSON(data)
    elif type(data) == list:
      self._initFromList(data)
    self.makeDirty()

  def __copy__(self):
    f = Feature(self._points.tolist())
    f._featureTransform = self._featureTransform
    return f

  def __deepcopy__(self, memo):
    return self.__copy__()

  def setTransformWithAxisAngle(self, axis, angle):
    """Sets the transform on the feature to a rotation about axis, by angle radians. Can be useful when
    measuring a feature that is rotating with a rotary axis."""
    self._featureTransform = metrology.helpers.makeRotationAxis(axis, angle)
    self.makeDirty()

  def makeDirty(self):
    """Clears any cached calculations, such as average position, best fit circle, etc. Automatically called after adding a point to the `Feature`."""
    self._average = None
    self._circle2D = None
    self._sphere = None
    self._line = None
    self._plane = None
    self._circle = None
    self._cylinder = None
    self._transformedPoints = None

  def addPoint(self, x, y, z):
    """
    Adds a point to the feature. Will clear any cached best fit feature calculations.
    """
    if len(self._points) == 0:
      self._points = np.append(self._points, np.array([x,y,z])).reshape(1,3)
      self._points.setflags(write=False)
    else:
      self._points = np.append(self._points, np.array([[x,y,z]]), axis=0)
      self._points.setflags(write=False)
    self.makeDirty()

    if _DEBUG:
      logger.debug("Points: ")
      for p in self._points:
        logger.debug("%s\t%s\t%s" % ( p[0], p[1], p[2] ))

  def clearPoints(self):
    """Removes all points from the feature."""
    self._points = np.array([])
    self.makeDirty()

    if _DEBUG:
      logger.debug("Cleared points!")

  def points(self):
    """Returns all the points with the `Feature`'s transform applied if the transform was specified. Simply returns the added points if
    no transform was specified."""
    if self._transformedPoints is None:
      if self._featureTransform is None:
        self._transformedPoints = np.array(self._points)
        self._transformedPoints.setflags(write=False)
      else:
        transformed = [ self._featureTransform @ [ p[0], p[1], p[2], 1 ] for p in self._points ]
        self._transformedPoints = np.array([ (p[0],p[1],p[2]) for p in transformed ])
        self._transformedPoints.setflags(write=False)

    return self._transformedPoints

  def first(self):
    """Returns the first point added to the Feature."""
    return self.points()[0]
    
  def average(self):
    """Returns the mathematical mean of the points: `np.array`([x, y, z])"""
    if self._average is None:
      self._average = self.points().mean(axis=0)

    if _DEBUG:
      logger.debug("Average: ", self._average)

    return self._average

  def plane(self):
    """Returns (pointOnPlane, normalOfPlane)"""
    if self._plane is None:
      self._plane = bestFitPlane(self.points())

    return self._plane

  def line(self):
    """Returns (pointOnLine, directionOfLine)"""
    if self._line is None:
      self._line = bestFitLine(self.points())

    if _DEBUG:
      logger.debug("Line: ", self._line)

    return self._line

  def cylinder(self, pt=None, axis=[0,0,1], radius=1):
    """Requires at least 7 points. Returns (pointOnMainAxis, directionOfMainAxis, radius)."""

    # Not caching as this best fit function takes float arguments. We either need to improve
    # how we cache, or for now, don't cache (see SOFT-1023).
    _cylinder = bestFitCylinder(self.points(), pt, axis, radius)

    if _DEBUG:
      logger.debug("Cylinder: ", _cylinder)

    return _cylinder

  def sphere(self):
    """Returns (radius, center)"""
    if self._sphere is None:
      self._sphere = skg.nsphere.nsphere_fit(self.points())

    if _DEBUG:
      logger.debug("Sphere: ", self._sphere)

    return self._sphere

  def circle(self):
    """Returns (radius, center, normalOfPlane)"""
    if self._circle is None:
      self._circle = metrology.bestFitCircle(self.points())

    if _DEBUG:
      logger.debug("Circle: ", self._circle)

    return self._circle

  def circle2D(self):
    """
    Returns (radius, center) of a circle using only the X and Y components of 
    the points.
    """

    if self._circle2D is None:
      ptData = self.points().T
      pts = np.array([ ptData[0],ptData[1] ]).T
      circle = skg.nsphere.nsphere_fit(pts)
      self._circle2D = (circle[0], circle[1])

    if _DEBUG:
      logger.debug("Circle2D: ", self._circle2D)

    return self._circle2D

  def projectToPlane(self, plane):
    """Returns a new `Feature` with all the points projected onto the provided plane. The plane argument must
    be specified as it is returned from the `Feature.plane()` method."""
    feat = Feature()
    points = self.points()

    for pt in points:
      proj_pt = projectPointToPlane(pt, plane)
      feat.addPoint(proj_pt[0], proj_pt[1], proj_pt[2])

    return feat

  def reverse(self):
    """Returns a new `Feature` with all the points reversed. This can be helpful for reversing the direction 
    of a best fit line, for example."""
    return Feature([ p for p in self.points()[::-1] ])

featureManagerInstance = None

def is_int(s):
  try:
    i = int(s)
    return True
  except:
    return False


class FeatureMap:
  """A key/value mapping for storing Features. This is meant to be used in an `oword.penta` or `namedparams.penta` context in
  combination with `FeatureManager`."""
  def __init__(self, data={}):
    self.features = {}

    for (key,value) in data.items():
      self.features[str(key)] = Feature(value)

    self.activeFeatureID = 0

  def getNextID(self):
    keys = [ int(k) for k in self.features.keys() if is_int(k) ]
    maxID = -1 if len(keys) == 0 else max(keys)
    return maxID+1

  def setNewActiveFeature(self):
    self.activeFeatureID = self.getNextID()

    return self.getActiveFeature()

  def setFeature(self, key, feat):
    if not isinstance(feat, Feature):
      raise TypeError("FeatureMap can only contain Features")

    fid = str(key)
    self.features[fid] = feat

  def setActiveFeatureID(self, fid):
    self.activeFeatureID = int(fid)

  def getActiveFeatureID(self):
    return self.activeFeatureID

  def __getattr__(self, key):
    """
    Gets the feature by fid, throwing an error if it doesn't exist.
    This is helpful calibration where we want an error to be thrown
    if the feature doesn't exist that we're trying to access, meaning
    the data hasn't been collected yet.
    """
    fid = str(key)
    return self.features[fid]

  def __getitem__(self, key):
    """
    Gets the feature by fid, throwing an error if it doesn't exist.
    This is helpful calibration where we want an error to be thrown
    if the feature doesn't exist that we're trying to access, meaning
    the data hasn't been collected yet.
    """
    fid = str(key)
    return self.features[fid]

  def getFeature(self, key):
    """
    Gets the feature by fid, returning an empty feature if it doesn't exist.
    This is helpful in G code where you can set the active feature to an integer
    and start adding points to it without worrying if it's been initialized.
    """
    fid = str(key)
    feature = self.features.get(fid, None)
    if feature == None:
      feature = Feature()
      self.features[fid] = feature

    return feature

  def getActiveFeature(self):
    return self.getFeature(self.activeFeatureID)

  def items(self):
    return self.features.items()

  def keys(self):
    return self.features.keys()

  def values(self):
    return self.features.values()


class FeatureManager:
  def __init__(self):
    self.sets = [ FeatureMap() ]

  def clear(self):
    self.sets.clear()
    self.sets.append( FeatureMap() )

  def push(self):
    """
    Pushes an empty FeatureMap to the top of the stack, making it the active FeatureMap in G code.
    This can be useful to ensure a subroutine or chunk of G code doesn't modify Features from a
    different context. 

    G code Example:

        ; Pushes a new feature set to be the active feature set
        o<push_feature_set> call

        ; Make any modifications to the active feature set by
        ; adding points to any number of features. In this case,
        ; we're simply creating a line. Normally, you would get
        ; this point data from a probe.
        o<add_point> call [0] [1] [2]
        o<add_point> call [1] [2] [3]
        o<add_point> call [4] [5] [6]

        ; Perform any calculations with those features. In this case,
        ; we're simply printing out a debug message with the line direction.
        (debug,Line Direction #<_penta_line_direction_x>, #<_penta_line_direction_y>, #<_penta_line_direction_z>)

        ; Pop the feature set stack, so it returns to the last active feature set.
        o<pop_feature_set> call

    Related: `FeatureManager.pop`, `oword.penta.push_feature_set`
    """
    self.sets.append( FeatureMap() )

  def pop(self):
    """
    Pops the active FeatureMap off the stack, making the previously active FeatureMap active in G code.
    This is used to clean up Features used in a local context, returning the FeatureManager to how it was
    before the local context modified it.

    G code Example:

        ; Pushes a new feature set to be the active feature set
        o<push_feature_set> call

        ; Make any modifications to the active feature set by
        ; adding points to any number of features. In this case,
        ; we're simply creating a line. Normally, you would get
        ; this point data from a probe.
        o<add_point> call [0] [1] [2]
        o<add_point> call [1] [2] [3]
        o<add_point> call [4] [5] [6]

        ; Perform any calculations with those features. In this case,
        ; we're simply printing out a debug message with the line direction.
        (debug,Line Direction #<_penta_line_direction_x>, #<_penta_line_direction_y>, #<_penta_line_direction_z>)

        ; Pop the feature set stack, so it returns to the last active feature set.
        o<pop_feature_set> call

    Related: `FeatureManager.push`, `oword.penta.pop_feature_set`
    """
    self.sets.pop()

  def getActiveFeatureMap(self):
    return self.sets[-1]

  def getInstance():
    global featureManagerInstance
    if featureManagerInstance == None:
      featureManagerInstance = FeatureManager()

    return featureManagerInstance
