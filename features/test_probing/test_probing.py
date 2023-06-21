#!/usr/bin/python3

import hal
import time
from scipy.spatial.transform import Rotation as R

h = hal.component("test-probing")

h.newpin("x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("tool-offset", hal.HAL_FLOAT, hal.HAL_IN)

h.newpin("probe-diameter", hal.HAL_FLOAT, hal.HAL_IN)
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

class RectangularBoreXY:
  def __init__(self, x,y,z,width,height,depth,hole_width,hole_height):
    x_thickness = .5*(width-hole_width)
    y_thickness = .5*(height-hole_height)
    self.top = AABB(x,y + .5*hole_height+.5*y_thickness,z,width,y_thickness,depth)
    self.bottom = AABB(x,y - .5*hole_height-.5*y_thickness,z,width,y_thickness,depth)

    self.left = AABB(x-.5*hole_width-.5*x_thickness,y,z, x_thickness, hole_height, depth)
    self.right = AABB(x+.5*hole_width+.5*x_thickness,y,z, x_thickness, hole_height, depth)

  def probe(self, x, y, z, diameter):
    return (self.top.probe(x,y,z,diameter) or 
            self.bottom.probe(x,y,z,diameter) or
            self.left.probe(x,y,z,diameter) or
            self.right.probe(x,y,z,diameter))

class RectangularBoreXYWithIsland:
  def __init__(self, x,y,z,width,height,depth,hole_width,hole_height,island_width, island_height):
    self.bore = RectangularBoreXY(x,y,z,width,height,depth,hole_width,hole_height)
    self.island = AABB(x,y,z,island_width,island_height,depth)

  def probe(self, x, y, z, diameter):
    return (self.bore.probe(x,y,z,diameter) or
            self.island.probe(x,y,z,diameter))

class RotatedObject:
  def __init__(self, obj, xRot,yRot,zRot):
    self.rot = R.from_euler("xyz", (xRot,yRot,zRot), degrees=True)
    self.obj = obj

  def probe(self, x,y,z,diameter):
    pt = self.rot.apply((x,y,z), inverse=True)

    return self.obj.probe(pt[0], pt[1], pt[2], diameter)


collisionTypes = {
# Won't trip probe at all
  0: NoCollisions(),
 
# 2" cube centered at origin
  1: AABB(0,0,0,2,2,2),

# 2" cube with 1" rectangular hole through it
  2: RectangularBoreXY(0,0,0,2,2,2,1,1),

# 2" cube with 1" rectangular hole through it, with .5" rectangular box through the center of the hole (so there is .25" channel around the central island) 
  3: RectangularBoreXYWithIsland(0,0,0,2,2,2,1,1,.5,.5),

# 2" cube rotated about Z 1 degree
  4: RotatedObject(AABB(0,0,0,2,2,2), 0,0,1),

# 2" cube with 1" rectangular hole through it rotated about Z 1 degree
  5: RotatedObject(RectangularBoreXY(0,0,0,2,2,2,1,1), 0,0,1)
}

try:
  while True:
    obj = collisionTypes[h["type"]]

    h["probe-output"] = obj.probe(h["x"], h["y"], h["z"] - h["tool-offset"], h["probe-diameter"])
    time.sleep(.01)

except KeyboardInterrupt:
  raise SystemExit

