# pytest test.py
import math
import random
import numpy as np
from pytest import approx

import metrology
import numpy

def test_angle_between_ccw_2d():
  line1 = [ 0, 1 ]
  line2 = [ -1, 0 ]

  assert metrology.angle_between_ccw_2d(line1, line2) == approx(90)

  line1 = [ .5*math.sqrt(2), .5*math.sqrt(2) ]
  line2 = [ 0, 1 ]
  assert metrology.angle_between_ccw_2d(line1, line2) == approx(45)

  line1 = [ .5*math.sqrt(2), .5*math.sqrt(2) ]
  line2 = [ -.5*math.sqrt(2), -.5*math.sqrt(2) ]
  assert metrology.angle_between_ccw_2d(line1, line2) == approx(180)

  line1 = [ 1, 0 ]
  line2 = [ -.5*math.sqrt(2), -.5*math.sqrt(2) ]
  assert 360+metrology.angle_between_ccw_2d(line1, line2) == approx(225)

def test_basic_3d_line_intersection():
  line1 = ( (0,0,0), (1,0,0) )
  line2 = ( (0,0,0), (0,0,1) )

  intersections = metrology.intersectLines(line1, line2)

  assert intersections[0] == approx((0,0,0))
  assert intersections[1] == approx((0,0,0))

def test_basic_3d_line_intersection2():
  line1 = ( (0,0,0), (1,0,0) )
  line2 = ( (20,20,20), (1,0,0) )

  intersections = metrology.intersectLines(line1, line2)

# infinite number of closest points, simply picks the one closest to origin point of line1
  assert intersections[0] == approx((0,0,0))
  assert intersections[1] == approx((0,20,20))

def test_basic_3d_line_intersection3():
  line1 = ((0,0,0), ( 1./math.sqrt(3), 1./math.sqrt(3), 1./math.sqrt(3) ))
  line2 = ((20,20,0), ( -1./math.sqrt(3), -1./math.sqrt(3), 1./math.sqrt(3) ))

  intersections = metrology.intersectLines(line1, line2)

  assert intersections[0] == approx(intersections[1])
  assert intersections[0] == approx((10,10,10))

def test_basic_3d_line_intersection_precision():

  for i in range(1000):
    while True:
      p1 = 100*np.random.rand(3)
      d1 = np.random.normal(size=3)
      line1 = (p1,d1/np.linalg.norm(d1))

      p2 = 100*np.random.rand(3)
      d2 = np.random.normal(size=3)
      line2 = (p2,d2/np.linalg.norm(d2))

      planeP = 100*np.random.rand(3)
      planeN = np.random.normal(size=3)
      planeN = planeN/np.linalg.norm(planeN)
      plane = (planeP,planeN)

      line3 = metrology.projectLineToPlane(line1, plane)
      line4 = metrology.projectLineToPlane(line2, plane)

      if abs(np.dot(line3[1],line4[1])) < 1 - 1e-6:
        # Do the calculations above until we have two lines that aren't parallel.
        # This will almost always be the case, but every once and a while they will
        # be parallel.
        break

    intersections = metrology.intersectLines(line3, line4)
    assert intersections[0] == approx(intersections[1])

def test_project_point_onto_xz_plane():
  plane = ( (0,0,0), (0,1,0) )
  point = ( 0,1,0)

  projected = metrology.projectPointToPlane(point, plane)

  assert projected == approx((0,0,0))

def test_project_point_onto_yz_plane():
  plane = ( (0,0,0), (1,0,0) )
  point = ( 1,0,0)

  projected = metrology.projectPointToPlane(point, plane)

  assert projected == approx((0,0,0))

def test_project_point_onto_xy_plane():
  plane = ( (0,0,0), (0,0,1) )
  point = ( 0,0,1)

  projected = metrology.projectPointToPlane(point, plane)

  assert projected == approx((0,0,0))

def test_3d_line_line_intersection():
  """This test uses an arbitrary plane and two lines that are mostly perpendicular to each other. The
     two lines are projected onto the plane. The shortest line segment that connects the resulting lines
     is calculated, defined by the closest point on each line. Those closest points should be the same
     point (within a tolerance), because they should intersect exactly (within the limits of floating 
     point math). This test was a real world use case that wasn't giving the right results, so I made
     it a test (the plane and line data were probed from the carabiner stock on the IMTS 2022 fixture). My
     original derivation of the line-line intersection had a flipped sign fairly early on and propagated 
     through to get the wrong results except in the most basic tests."""

  plane = ( (4.059958,1.904661,3.980913), (-0.6387421383884229,-0.36188344887474067,0.6790057805921152) )

  assert numpy.linalg.norm(plane[1]) == approx(1)

  line1 = ( (4.35629611e+00, -1.30500374e-03,  3.31362159e+00), (0.65058066, 0.34757243, 0.67523196) )

  assert numpy.linalg.norm(line1[1]) == approx(1)

  line2 = ( (4.0599579 , 1.90466099, 3.98091324), (-0.47716853,  0.87876671,  0.00890289) )

  assert numpy.linalg.norm(line2[1]) == approx(1)

  line3 = metrology.projectLineToPlane(line1, plane)
  line4 = metrology.projectLineToPlane(line2, plane)

  assert numpy.linalg.norm(line3[1]) == approx(1)
  assert numpy.linalg.norm(line4[1]) == approx(1)

  assert numpy.dot(line3[1], plane[1]) == approx(0)
  assert numpy.dot(line4[1], plane[1]) == approx(0)

  assert numpy.dot(line3[1], line4[1]) < 1 - 1e-6

  intersections = metrology.intersectLines(line3, line4)

  assert intersections[0] == approx(intersections[1])

def test_best_fit_sphere():
  points = [ (1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1) ]
  feature = metrology.Feature(points)
  sphere = feature.sphere()

  assert sphere[0] == approx(1)
  assert sphere[1] == approx((0,0,0))

def test_best_fit_sphere_random4():
  for j in range(1000):
    pts = []
    for i in range(4):
      needNewPt = True
      while needNewPt:
        a = random.random()
        b = random.random()
        theta = 2*math.pi*a
        phi = math.acos(2*b-1)
        sinPhi = math.sin(phi)
        cosPhi = math.cos(phi)
        sinTheta = math.sin(theta)
        cosTheta = math.cos(theta)
        pt = (sinPhi * cosTheta, sinPhi * sinTheta, cosPhi)

        for existingPt in pts:
          if pt == approx(existingPt, abs=1e-2):
            needNewPt = True
            break
        if len(pts) == 3:
          # Can't have 4 co-planar points, so pick another point if this one is close to coplanar with the other 3.
          # If we don't do this, floating point errors can make the sphere asserts below fail without a larger
          # floating point tolerance. Since the 4 points that define a sphere shouldn't be coplanar, this seems
          # like the best place to increase the tolerance.
          planeFeature = metrology.Feature(pts)
          projectedPt = metrology.projectPointToPlane(pt, planeFeature.plane())
          if projectedPt == approx(pt, abs=1e-2):
            needNewPt = True
          else:
            needNewPt = False
        else:
          needNewPt = False

      pts.append(pt)

    feature = metrology.Feature(pts)
    sphere = feature.sphere()

    assert sphere[0] == approx(1)
    assert sphere[1] == approx((0,0,0))

def test_best_fit_sphere_random_radius():
  tol = 2e-4
  repeatability = .5e-4
  for j in range(1000):
    pts = []
    for i in range(100):
      a = random.random()
      b = random.random()
      theta = 2*math.pi*a
      phi = math.acos(2*b-1)
      sinPhi = math.sin(phi)
      cosPhi = math.cos(phi)
      sinTheta = math.sin(theta)
      cosTheta = math.cos(theta)
      r = random.normalvariate(1, repeatability)
      pt = (r*sinPhi * cosTheta, r*sinPhi * sinTheta, r*cosPhi)

      pts.append(pt)

    feature = metrology.Feature(pts)
    sphere = feature.sphere()

    assert sphere[0] == approx(1.0, abs=tol)
    assert sphere[1] == approx((0.0,0.0,0.0), abs=tol)

def test_best_fit_line():
  pts = [ (0.0,0.0,0.0), (1.0,1.0,1.0) ]
  feature = metrology.Feature(pts)
  line = feature.line()

  assert line[0] == approx((.5, .5, .5))
  assert line[1] == approx((1./math.sqrt(3), 1./math.sqrt(3), 1./math.sqrt(3)))

def test_best_fit_line_direction_matches_order():
  for j in range(1000):
    pt = (1000*random.random(), 1000*random.random(), 1000*random.random())
    dir = (2*random.random()-1, 2*random.random()-1, 2*random.random()-1)

    pts = []
    for i in range(10):
      p = numpy.add(pt, numpy.multiply(dir, i))
      pts.append(p)

    normalizedDir = numpy.array(dir)/numpy.linalg.norm(dir)

    feature = metrology.Feature(pts)
    line = feature.line()

    assert line[1] == approx(normalizedDir)

def test_best_fit_line_direction_matches_order_edge_case():
  """We found our best fit line function produces the same output whether
  this specific pts array is provided in order or reversed when we would
  expect reversing the order to reverse the line. Seems like we made incorrect
  assumptions about the best fit line calculation and need to explicitly check 
  the direction. See changes to bestFitLine made in the same commit this test 
  was added, which makes this test pass when it previously failed."""

  pts = [
    [-133.51666032,   -8.65792664, -110.97359563],
    [-133.51494674,  -25.59015299, -110.97515438],
    [-133.51413513,  -42.52348536, -110.97943219],
    [-133.51374911,  -59.45522886, -110.98192507],
    [-133.51390869,  -76.38668506, -110.98622678],
    [-133.51305754,  -93.32001301, -110.98944711],
    [-133.51609944, -110.25519564, -110.98932217]
  ]

  feature = metrology.Feature(pts)
  feature_rev = metrology.Feature(list(reversed(pts)))

  line = feature.line()
  line_rev = feature_rev.line()
  assert line[1] == approx(-line_rev[1])
