# From https://github.com/cjekel/cjekel.github.io/blob/master/assets/2015-09-13/demo.py

# The MIT License (MIT)
# 
# Copyright (c) 2015 Cactus Authors - https://github.com/koenbok/Cactus/blob/master/AUTHORS -  Released under the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np

#	fit a sphere to X,Y, and Z data points
#	returns the radius and center points of
#	the best fit sphere
def sphereFit(spX,spY,spZ):
  #   Assemble the A matrix
  A = np.zeros((len(spX),4))
  A[:,0] = spX*2
  A[:,1] = spY*2
  A[:,2] = spZ*2
  A[:,3] = 1

  #   Assemble the f matrix
  f = np.zeros((len(spX),1))
  f[:,0] = (spX*spX) + (spY*spY) + (spZ*spZ)
  C, residules, rank, singval = np.linalg.lstsq(A,f)

  #   solve for the radius
  t = (C[0]*C[0])+(C[1]*C[1])+(C[2]*C[2])+C[3]
  radius = np.sqrt(t)

  return (radius[0], (C[0][0], C[1][0], C[2][0]))
