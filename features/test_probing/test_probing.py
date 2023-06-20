#!/usr/bin/python3

import hal
import time

h = hal.component("test-probing")

h.newpin("x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("tool-offset", hal.HAL_FLOAT, hal.HAL_IN)

h.newpin("probe-diameter", hal.HAL_FLOAT, hal.HAL_IN)

# different types of objects
# 0 - No collision object
# 1 - 2" cube, centered at origin
h.newpin("type", hal.HAL_S32, hal.HAL_IN)

h.newpin("probe-output", hal.HAL_BIT, hal.HAL_OUT)

h.ready()

class NoCollisions:
  def __init__(self):
    pass

  def probe(self,x,y,z,diameter):
    return False


class AABB:
  def __init__(self,x,y,z,width,height,depth):
    self.xMin = x-width*.5
    self.xMax = x+width*.5
    self.yMin = y-height*.5
    self.yMax = y+height*.5
    self.zMin = z-depth*.5
    self.zMax = z+depth*.5

  def closestPointInAABB(self,x,y,z):
    closestX = x
    if closestX < self.xMin:
      closestX = self.xMin

    if closestX > self.xMax:
      closestX = self.xMax

    closestY = y
    if closestY < self.yMin:
      closestY = self.yMin

    if closestY > self.yMax:
      closestY = self.yMax

    closestZ = z
    if closestZ < self.zMin:
      closestZ = self.zMin

    if closestZ > self.zMax:
      closestZ = self.zMax

    return (closestX, closestY, closestZ)

  def probe(self, x,y,z,diameter):
    """Returns true if a touch probe with provided diameter with its center at x,y,z would intersect the cube's volume."""

    closest = self.closestPointInAABB(x,y,z)

    dx = closest[0]-x
    dy = closest[1]-y
    dz = closest[2]-z

    sqDist = dx*dx+dy*dy+dz*dz
    r = diameter*.5

    return sqDist <= r*r

# TODO - add more collision objects and use them based on type pin
noCollisions = NoCollisions()
cubeObject = AABB(0,0,0,2,2,2)

collisionTypes = {
  0: noCollisions,
  1: cubeObject
}

try:
  while True:
    obj = collisionTypes[h["type"]]

    h["probe-output"] = obj.probe(h["x"], h["y"], h["z"] - h["tool-offset"], h["probe-diameter"])
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit

