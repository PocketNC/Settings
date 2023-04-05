from pytest import approx

import math
import random
import kinematics

def test_direction_xyzbc_local_to_global_transform():
  dirx = -0.6123720407485962
  diry = -0.3535532057285309
  dirz = -0.7071071863174438

  newDir = kinematics.transform_direction_local_to_global("xyzbc-trt-kins", [0,0,0,0,45,-30], dirx, diry, dirz)
  assert newDir == approx((-1,0,0), abs=1e-6)

def test_xyzbc_direction_transformations():

  for i in range(1000):
    while True:
      dirx = 2*random.random()-1
      diry = 2*random.random()-1
      dirz = 2*random.random()-1

      if dirx > 1e-6 or diry > 1e-6 or dirz > 1e-6:
        break

    mag = math.sqrt(dirx*dirx+diry*diry+dirz*dirz)
    dirx /= mag
    diry /= mag
    dirz /= mag

    B = 290*random.random()-145
    C = 360*random.random()
    globalDir = kinematics.transform_direction_local_to_global("xyzbc-trt-kins", [0,0,0,0,B,C], dirx, diry, dirz)
    localDir = kinematics.transform_direction_global_to_local("xyzbc-trt-kins", [0,0,0,0,B,C], globalDir[0], globalDir[1], globalDir[2])

    assert localDir == approx((dirx,diry,dirz))

