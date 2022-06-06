from typing import Optional, Sequence, Tuple, Union, Iterable, SupportsFloat, Dict, List, Any, Callable 
from enum import Enum
import enum
import math
from .braids.fscad.src.fscad import fscad as fscad
# from . import highlight as highlight
# from .highlight import highlight
import itertools
import re
import adsk.fusion, adsk.core


from math import sin,cos,tan

import numpy as np


from numpy.typing import ArrayLike


from .utility import *

class ToughCaseModule ( MutableComponentWithCachedBodiesAndArbitraryBodyHash ) :
    def __init__(self,

        name                                               : Optional[str]  = None ,
    ):
        
        self.dovetailPitch : float = 11.7 * millimeter
        # d1

        self.dovetailHeight : float = 17.45 * millimeter
        # d5

        self.d7 : float = ( 10.30 * millimeter - 6.22 * millimeter )/2
        self.d8 : float = mean (
            math.atan( (7.18 * millimeter - 5.25 * millimeter) / 2 / self.d7 ) * radian,
            math.atan( (5.44 * millimeter - 3.55 * millimeter) / 2 / self.d7 ) * radian
        )
        self.d9 : float = mean (
            math.atan( (7.13 * millimeter - 5.47 * millimeter) / 2 / self.dovetailHeight ) * radian
        )
        
        self.dividerSpineThickness : float = 6.27 * millimeter # measured
        # d11

        self.d12 : float = zeroLength # guess
        self.d13 : float = 2 * millimeter # guess
        self.caseWallThickness = 2 * millimeter
        #d14

        self.caseDovetailCountX : int = 11 
        # exactly how many dovetails we consider ourselves to have along x is a
        # bit of an open question, but whatever the formula relating
        # dovetailCount and caseExtentX ends up being, this parameter will step
        # the the extent by one dovetailPitch.

        # self.caseDovetailCountY : int = 13 
        # exactly how many dovetails we consider ourselves to have along y is a
        # bit of an open question, but whatever the formula relating
        # dovetailCount and caseExtentY ends up being, this parameter will step
        # the the extent by one dovetailPitch.

        # self.d15 : float = self.dovetailPit
        # # clearance offset as manufactured

        self.d16 = self.dovetailPitch - (self.dividerSpineThickness + 2*self.d7)

        self.d2 : float = self.dovetailPitch/2 - self.dovetailHeight * tan(self.d9) + self.d7 * tan(self.d8)
        # minus, plus

        self.d3 : float = self.dovetailPitch/2 - self.dovetailHeight * tan(self.d9) - self.d7 * tan(self.d8)
        # minus, minus

        self.d6 : float = self.dovetailPitch/2 + self.dovetailHeight * tan(self.d9) + self.d7 * tan(self.d8)
        # plus, plus 

        self.d10 : float = self.dovetailPitch/2 + self.dovetailHeight * tan(self.d9) - self.d7 * tan(self.d8)
        # plus, minus

        self.d4 : float = self.d3

        self.caseInteriorExtentX = (2*self.d7 + self.d12)*2 + self.dividerSpineThickness + self.caseDovetailCountX * self.dovetailPitch
        self.caseInteriorExtentY = 123.123 * millimeter # bogus

        print(f"d8: {self.d8/degree} degrees")
        print(f"d9: {self.d9/degree} degrees")

        super().__init__(name)

    
    def _make_raw_bodies(self) -> Sequence[adsk.fusion.BRepBody]:
        returnValue : list[adsk.fusion.BRepBody] = []

        dovetail : fscad.Component = fscad.Loft(
            #zMinSheet:
            fscad.Polygon(
                adsk.core.Point3D.create( 0       , -self.d10 /2  , 0       ),
                adsk.core.Point3D.create( self.d7 , -self.d6  /2  , 0       ),
                adsk.core.Point3D.create( self.d7 , +self.d6  /2  , 0       ),
                adsk.core.Point3D.create( 0       , +self.d10 /2  , 0       )
            ),
                        
            #zMaxSheet: 
            fscad.Polygon(
                adsk.core.Point3D.create( 0       , -self.d3  /2  , self.dovetailHeight ),
                adsk.core.Point3D.create( self.d7 , -self.d2  /2  , self.dovetailHeight ),
                adsk.core.Point3D.create( self.d7 , +self.d2  /2  , self.dovetailHeight ),
                adsk.core.Point3D.create( 0       , +self.d3  /2  , self.dovetailHeight )
            )
        )

        cavityBase = fscad.Rect(
                self.caseInteriorExtentX, 
                self.caseInteriorExtentY
            )

        highlight(cavityBase)

        cavity  = fscad.Extrude(
            cavityBase,
            height=self.dovetailHeight
        )
        
        case = fscad.Thicken(
            itertools.chain(
                cavity.side_faces,
                cavity.start_faces
            ), 
            thickness=self.caseWallThickness
        )
        

        returnValue += [
            fscad.brep().copy(body.brep) 
            for component in [
                dovetail, 
                case
            ]
            for body in component.bodies
        ]

        return returnValue
