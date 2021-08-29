from typing import Optional, Sequence, Union
from enum import Enum
import enum
import math
import functools
import scipy
# the above import of scipy requires the user to have taken action to ensure that scipy is available somewhere on the system path,
# for instance by doing "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install scipy
# I would like to automate the management of dependencies like this.  With a "normal" Python project, pipenv would be the logical way to do it,
# but for scripts that are to be loaded by fusion, it is unclear what the best way to manage dependencies is -- maybe some sort of vendoring?


import numpy as np
# I am relying on the installation of scipy to also install numpy.

from numpy.typing import ArrayLike, NDArray
from typing import SupportsFloat
from numpy import ndarray
from numpy import number
from math import sin, cos
import unyt
import operator
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt

radian = 1
degree = math.pi/180 * radian
centimeter = 1 #fusion's internal native length unit is the centimeter
millimeter = 0.1 * centimeter
zeroLength = 0 
meter = 1000 * millimeter
inch = 25.4 * millimeter
# this is for compatability with expressions copied from featureScript, wherein length is a special type, and I anticipate that
# we will eventually use a similar system of units where we will want a zeroLength.

# we would benefit from having an organized system of physical units.  For now, I am implicitly assuming that all distance units are millimeters.

xHat = np.array((1,0,0))
yHat = np.array((0,1,0))
zHat = np.array((0,0,1))



def norm(v : ndarray) -> number :
    # v is intended to be a rank-one array with real elements
    # being able to specify size and rank (i.e. array 'shape' in numpy parlance) as a type is sorely needed -- actually, it looks like numpy.typing.NDArray comes pretty close.
    # ought to handle zero vectors, or at least throw a meaningful exception
    # according to https://stackoverflow.com/questions/21030391/how-to-normalize-an-array-in-numpy-to-a-unit-vector ,
    # , it is slightly faster to compute the norm as np.sqrt((v*v).sum()) than to call np.linalg.norm()
    return np.sqrt((v*v).sum())

def normalized(v : ndarray) -> ndarray:
    # v is intended to be a rank-one array with real elements
    # being able to specify size and rank (i.e. array 'shape' in numpy parlance) as a type is sorely needed.
    # ought to handle zero vectors, or at least throw a meaningful exception
    # ought to handle the case of complex elements
    # It might improve performance to have a flag to track whether a vector is already normalized, to avoid re-doing the computation unnecessarily.
    return v/norm(v)

normalize = normalized

def rotationMatrix3d(axisOfRotation : ndarray, angleOfRotation : number) -> ndarray:
    # compute normalized axisOfRotation and call it v:
    v = normalized(axisOfRotation)
    projectOnV=np.array(
        [
            [  v[0]*v[0],  v[0]*v[1],  v[0]*v[2]  ],
            [  v[0]*v[1],  v[1]*v[1],  v[1]*v[2]  ],
            [  v[0]*v[2],  v[1]*v[2],  v[2]*v[2]  ]
        ]
    )
    oneMinusProjectOnV=np.array(
        [
            [  1 -v[0]*v[0]  ,    -v[0]*v[1]  ,    -v[0]*v[2]  ],
            [    -v[0]*v[1]  ,  1 -v[1]*v[1]  ,    -v[1]*v[2]  ],
            [    -v[0]*v[2]  ,    -v[1]*v[2]  ,  1 -v[2]*v[2]  ]
        ]
    )
    # I am not sure which is more computationally efficient: 1 -v[0]*v[0]  or v[1]*v[1] + v[2]*v[2] .  
    # They should give the equivalent numerical result due to v being normalized.

    # projectOnV=np.array(
    #     [
    #         [  v[0]**2,  v[0]*v[1],  v[0]*v[2]  ],
    #         [  v[0]*v[1],  v[1]**2,  v[1]*v[2]  ],
    #         [  v[0]*v[2],  v[1]*v[2],  v[2]**2  ]
    #     ]
    # )
    # oneMinusProjectOnV=np.array(
    #     [
    #         [  1 -v[0]**2  ,    -v[0]*v[1]  ,    -v[0]*v[2]  ],
    #         [    -v[0]*v[1]  ,  1 -v[1]**2  ,    -v[1]*v[2]  ],
    #         [    -v[0]*v[2]  ,    -v[1]*v[2]  ,  1 -v[2]**2  ]
    #     ]
    # )

    vCross=np.array(
        [
            [   0     ,  -v[2]  ,   v[1]  ],
            [   v[2]  ,   0     ,  -v[0]  ],
            [  -v[1]  ,   v[0]  ,   0     ]
        ]
    )
    return projectOnV + cos(angleOfRotation) * oneMinusProjectOnV + sin(angleOfRotation) * vCross

def floor(x : SupportsFloat, modulus : SupportsFloat = 1 ) -> SupportsFloat :
    """this is a two-argument version of the floor function that lets you specify a modulus other than 1, if so desired"""
    return math.floor(x/modulus) * modulus 

def mean(*args: ArrayLike) -> ArrayLike:
    # return functools.reduce(operator.add, args)/len(args)
    return sum(args)/len(args)

def vector(*args) -> ndarray:
    return np.array(args)


