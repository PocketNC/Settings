import numpy
import math

# Adapted from three.js
# https://github.com/mrdoob/three.js/blob/dev/src/math/Matrix4.js

# The MIT License
# 
# Copyright © 2010-2022 three.js authors
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

def makeRotationAxis(axis, angle):
  c = math.cos(angle)
  s = math.sin(angle)
  t = 1 - c
  x = axis[0]
  y = axis[1]
  z = axis[2]
  tx = t * x
  ty = t * y

  return numpy.array([ [ tx * x + c, tx * y - s * z, tx * z + s * y, 0 ],
                       [ tx * y + s * z, ty * y + c, ty * z - s * x, 0 ],
                       [ tx * z - s * y, ty * z + s * x, t * z * z + c, 0 ],
                       [ 0, 0, 0, 1 ] ])
