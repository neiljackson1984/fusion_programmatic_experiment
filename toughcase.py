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

        # self.d15 : float = self.dovetailPitch
        # # clearance offset as manufactured

        self.d16 = self.dovetailPitch - (self.dividerSpineThickness + 2*self.d7)

        self.d17 : float =  3.5 * millimeter #eyeballed
        self.d18 : float =  3.5 * millimeter #eyeballed

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

        self.dovetailRailIntervalPitchCounts : int = 6
        self.dovetailRailInterval : float = 2*self.d7 + self.d12 + self.dovetailRailIntervalPitchCounts * self.dovetailPitch


        print(f"dovetailRailInterval: {self.dovetailRailInterval/millimeter} millimeters")
        print(f"dovetailRailInterval - 2*d7: {(self.dovetailRailInterval - 2*self.d7)/millimeter} millimeters")
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

        # highlight(cavityBase)

        cavity  = fscad.Extrude(
            cavityBase,
            height=self.dovetailHeight
        )

        dovetailPlacements : Sequence[adsk.core.Matrix3D] = []

        yDovetailPositionsY = np.arange(
            start = (
                cavity.min().y 
                + remainder(
                    2*self.d7 + self.d13 + self.dividerSpineThickness/2 + self.dovetailPitch/2,
                    modulus = self.dovetailPitch
                )
            ),
            stop = cavity.max().y ,
            step = self.dovetailPitch
        )
        yDovetailPlacements : Sequence[adsk.core.Matrix3D] = [
             rigidTransform3D(
                xDirection = (1 if wallIndex else -1) * xHat, 
                zDirection = zHat,
                origin=(
                    (cavity.min().x if wallIndex else cavity.max().x), 
                    positionY, 
                    cavity.min().z 
                )
             )
             for positionY in yDovetailPositionsY
             for wallIndex in (0,1)
        ]
        yDovetails : fscad.Component = fscad.BRepComponent(
            *(
                body.brep
                for t in yDovetailPlacements
                for body in dovetail.copy().transform(t).bodies
            )
        )
        yDovetailsMask = boxByCorners(
            corner1 = castTo3dArray(cavity.min()) + self.d17 * yHat,
            corner2 = castTo3dArray(cavity.max()) - self.d17 * yHat
        )
        yDovetails = fscad.Intersection(yDovetails, yDovetailsMask)

        xDovetailPositionsX = np.arange(
            start = (
                cavity.min().x 
                + remainder(
                    2*self.d7 + self.d12 + self.dividerSpineThickness/2 + self.dovetailPitch/2,
                    modulus = self.dovetailPitch
                )
            ),
            stop = cavity.max().x,
            step = self.dovetailPitch
        )
        xDovetailPlacements : Sequence[adsk.core.Matrix3D] = [
             rigidTransform3D(
                xDirection = (1 if wallIndex else -1) * yHat, 
                zDirection = zHat,
                origin=(
                    positionX, 
                    (cavity.min().y if wallIndex else cavity.max().y), 
                    cavity.min().z 
                )
             )
             for positionX in xDovetailPositionsX
             for wallIndex in (0,1)
        ]
        xDovetails : fscad.Component = fscad.BRepComponent(
            *(
                body.brep
                for t in xDovetailPlacements
                for body in dovetail.copy().transform(t).bodies
            )
        )
        xDovetailsMask = boxByCorners(
            corner1 = castTo3dArray(cavity.min()) + self.d18 * xHat,
            corner2 = castTo3dArray(cavity.max()) - self.d18 * xHat
        )
        xDovetails = fscad.Intersection(xDovetails, xDovetailsMask)

        
        case = fscad.Thicken(
            itertools.chain(
                cavity.side_faces,
                cavity.start_faces
            ), 
            thickness=self.caseWallThickness
        )
        case = fscad.Union(case, yDovetails, xDovetails)


        dividerSpineStation : int = self.dovetailRailIntervalPitchCounts
        dividerSpinePositionX : float = min(xDovetailPositionsX) + ( dividerSpineStation + 1/2)*self.dovetailPitch
        dividerSpineCore = boxByCorners(
            corner1 = (
                -self.dividerSpineThickness/2,
                self.d7,
                zeroLength
            ),
            corner2 = (
                +self.dividerSpineThickness/2,
                self.caseInteriorExtentY - self.d7,
                self.dovetailHeight + 3.1234 * millimeter # TODO parameterize this height
            )
        )
        dividerSpineXDovetailPlacements : Sequence[adsk.core.Matrix3D] = [
             rigidTransform3D(
                xDirection = (1 if wallIndex else -1) * yHat, 
                zDirection = -zHat,
                origin=(
                    zeroLength, 
                    (dividerSpineCore.max().y if wallIndex else dividerSpineCore.min().y), 
                    self.dovetailHeight 
                )
             )
             for wallIndex in (0,1)
        ]
        dividerSpineXDovetails : fscad.Component = fscad.BRepComponent(
            *(
                body.brep
                for t in dividerSpineXDovetailPlacements
                for body in dovetail.copy().transform(t).bodies
            )
        )
        

        dividerSpineYDovetailPlacements : Sequence[adsk.core.Matrix3D] = [
             rigidTransform3D(
                xDirection = (-1 if wallIndex else 1) * xHat, 
                zDirection = zHat,
                origin=(
                    (-1 if wallIndex else 1) * self.dividerSpineThickness/2, 
                    positionY, 
                    zeroLength
                )
             )
             for positionY in yDovetailPositionsY
             for wallIndex in (0,1)
        ]
        dividerSpineYDovetails : fscad.Component = fscad.BRepComponent(
            *(
                body.brep
                for t in dividerSpineYDovetailPlacements
                for body in dovetail.copy().transform(t).bodies
            )
        )
        dividerSpineYDovetailsMask = boxByCorners(
            corner1 = (
                dividerSpineYDovetails.min().x,
                self.d17,
                dividerSpineYDovetails.min().z

            ),
            corner2 = (
                dividerSpineYDovetails.max().x,
                self.caseInteriorExtentY - self.d17,
                dividerSpineYDovetails.max().z
            )
        )
        dividerSpineYDovetails = fscad.Intersection(dividerSpineYDovetails, dividerSpineYDovetailsMask)

        dividerSpine = fscad.Union(dividerSpineCore, dividerSpineXDovetails, dividerSpineYDovetails)
        dividerSpine.translate(tx = dividerSpinePositionX)

        returnValue += [
            fscad.brep().copy(body.brep) 
            for component in [
                # xDovetails, 
                # yDovetails,
                case,
                dividerSpine
            ]
            for body in component.bodies
        ]

        return returnValue
