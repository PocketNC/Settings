# Adapted from https://scipy-cookbook.readthedocs.io/items/Least_Squares_Circle.html
# https://github.com/scipy/scipy-cookbook/blob/main/ipython/Least_Squares_Circle.ipynb

# Copyright (c) 2001, 2002 Enthought, Inc.
# All rights reserved.
# 
# Copyright (c) 2003-2017 SciPy Developers.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of Enthought nor the names of the SciPy Developers
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

import numpy
from scipy import optimize

def calculate(pts):
  """pts is an array of (x,y) points, returns tuple with center and radius ((xc,yc), r)"""
  pts_array = numpy.array(pts)

  x = pts_array.T[0]
  y = pts_array.T[1]

  x_m = numpy.mean(x)
  y_m = numpy.mean(y)

  def distFromPoint(xc, yc):
    """ calculate the distance of each 2D points from the center (xc, yc) """
    return numpy.sqrt((x-xc)**2 + (y-yc)**2)


  def distFromMean(c):
    """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
    distances = distFromPoint(*c)
    return distances - distances.mean()

  def jacobianOfDistFromMean(c):
    """ Jacobian of f_2b
  The axis corresponding to derivatives must be coherent with the col_deriv option of leastsq"""
    xc, yc = c
    jacobian = numpy.empty((len(c), x.size))

    distances = distFromPoint(xc, yc)
    jacobian[0] = (xc - x)/distances                   # dR/dxc
    jacobian[1] = (yc - y)/distances                   # dR/dyc
    jacobian    = jacobian - jacobian.mean(axis=1)[:, None]

    return jacobian

  (center, ier) = optimize.leastsq(distFromMean, (x_m, y_m), Dfun=jacobianOfDistFromMean, col_deriv=True)

  return ( (center[0], center[1]), distFromPoint(center[0], center[1]).mean())
