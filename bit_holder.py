from typing import Optional, Sequence, Tuple, Union, Iterable, SupportsFloat, Dict, List
from enum import Enum
import enum
import math
from .braids.fscad.src.fscad import fscad as fscad
from . import highlight as highlight
# from .highlight import highlight
import itertools
import re
import adsk.fusion, adsk.core

# import scipy
# the above import of scipy requires the user to have taken action to ensure that scipy is available somewhere on the system path,
# for instance by doing "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install scipy
# I would like to automate the management of dependencies like this.  With a "normal" Python project, pipenv would be the logical way to do it,
# but for scripts that are to be loaded by fusion, it is unclear what the best way to manage dependencies is -- maybe some sort of vendoring?

from math import sin,cos,tan

import numpy as np


from numpy.typing import ArrayLike


from .bit_holder_utility import *


_cannedBitHolders : Dict[str, 'BitHolder'] = {}

## regex substitution rules that were useful when converting the original featurescript code to python: 
 # \bthis\[\]\.get_(\w+)\(\)
 # ==>
 # self.$1
 
 # \bthis\[\]\.get_(\w+) = 
 # ==>
 # @property\n    def $1(self)
 
 # \b(?<containerName>(?<this>this)|(?:\w+))\[\]\.get_(?<propertyName>\w+)\(\)
 # ==>
 # (?{this}self:$+{containerName}).$+{propertyName}
 
 # mean\(
 # ==>
 # np.mean(

class LabelSculptingStrategy(Enum):
    EMBOSS = enum.auto()
    ENGRAVE = enum.auto()
     
class MountHolesPositionZStrategy(Enum):
    # mountHolesPositionZSpecifier controls how the z position of the mount holes is determined.
    # the allowable values are 
    #  1) the string "grazeBottomOfSaddleBoreLip", which will cause the mount hole z position to be determined automatically so that the counterbore of the mount hole is tangent to the bottom lip of the socket bore lip.
    #  2)  the string "middle", which will cause the mount hole z position to be placed in the middle of the bit holder.
    #  3)  a valueWithUnits (e.g. -2 * millimeter), which will simply force the mount holes to be placed at the specified z coordinate (as measured in the frame of the bit holder).
    # Note: for porting to Fusion, I am changing this protocol a bit; now, case 3 is to use the "explicit" value o fhtis enum,
    # and specify the actual value with a separate property of the BitHolder object.
    grazeBottomOfSaddleBoreLip = enum.auto()
    middle = enum.auto()
    explicit = enum.auto()

class ProtrusionStrategy(Enum):
    explicitProtrusion = enum.auto()
    explicitEmbedment = enum.auto()

class Bit :
    """ a bit is essentially a cylinder along with a labelText property -- for our 
    purposes, these are the only aspects of a bit that we care about."""


    def __init__(self,
        outerDiameter : float = 17 * millimeter,
        length        : float = 25 * millimeter,
        labelText     : str   = "DEFAULT"
    ):
        self.outerDiameter  : float = outerDiameter
        self.length         : float = length
        self.labelText      : str   = labelText

class Socket (Bit):
    """ Socket is a specialized type of (i.e. inherits from) Bit. the only
    thing that socket does differently is that it overrides the
    labelText property, and defines a couple of other properties to
    help specify labelText.
    """
    def __init__(self, 
        outerDiameter      : float          = 17 * millimeter,
        length             : float          = 25 * millimeter,
        # the above arguments are passed unaltered to the constructor of the super class.

        nominalSize        : float = 3/8 * inch,
        # the nominal size of the head of the fastener that this socket is intended to drive.

        nominalUnit       : float = 1 * inch,
        # specifies the system of units (typically, imperial or metric) that this socket
        # is designed for.  This influences labelText.
        # in practice, nominalUnit is expected to be either 1 * inch or 1 * millimeter.

        driveSize          : float = 1/2 * inch,
        # the nominal size of the square nub.  This is used to categorize the sockets.

        explicitLabelText  : Optional[str]  = None
        # iff it is truthy, explicitLabelText will override the otherwise automatically-computed labelText.
    ):
        # super().__init__(
        #     outerDiameter = outerDiameter,
        #     length = length
        # )
        self.outerDiameter  : float = outerDiameter
        self.length         : float = length

        self.nominalSize        : float          = nominalSize
        self.nominalUnit        : unyt.Unit      = nominalUnit
        self.driveSize          : float          = driveSize
        self.explicitLabelText  : Optional[str]  = explicitLabelText

    # I am assuming and hoping that the labelText method, declared with
    # @property decorator, will override the simple labelText property defined
    # in the constructor of the super class, but we should confirm this.
    @property
    def labelText(self) -> str:
        if self.explicitLabelText:
            return self.explicitLabelText
        
        unitlessSize = self.nominalSize / self.nominalUnit
        if self.nominalUnit == 1 * inch:
            return toProperFractionString(unitlessSize, 64) + "\n" + "in"
        elif self.nominalUnit == 1 * millimeter:
            unitlessSize = round(unitlessSize, 1)
            if unitlessSize == int(unitlessSize):
                unitlessSize = int(unitlessSize)
            return f"{unitlessSize}" + "\n" + "mm"
        # this is the ratio of nominalSize to one nominalUnit.

class BitHolderSegment (fscad.Component)  :
    def __init__(self, 
        bit                                                : Optional[Bit]           = None,
        bitHolder                                          : Optional['BitHolder']   = None,
        angleOfElevation                                   : float                   = 45   * degree,
        lecternAngle                                       : float                   = 45   * degree,
        lecternMarginBelowBore                             : float                   = 3    * millimeter,
        lecternMarginAboveBore                             : float                   = 3    * millimeter,
        boreDiameterAllowance                              : float                   = 0.8  * millimeter,
        mouthFilletRadius                                  : float                   = 2    * millimeter,
        explicitBitProtrusion                              : float                   = 10.6 * millimeter,
        explicitBitEmbedment                               : float                   = 12.345 * millimeter,
        bitProtrusionStrategy                              : ProtrusionStrategy      = ProtrusionStrategy.explicitProtrusion,

        labelExtentZ                                       : float                   = 12   * millimeter,
        labelThickness                                     : float                   = 0.9  * millimeter,
        #this is the thickness of the text (regardless of whether the text is engraved or embossed).
                                 
        labelZMax                                          : float                   = -1   * millimeter,
        labelFontHeight                                    : float                   = 4.75 * millimeter,
        labelFontName                                      : str                     = "Arial", #"NotoSans-Bold.ttf"
        labelSculptingStrategy                             : LabelSculptingStrategy  = LabelSculptingStrategy.ENGRAVE, # labelSculptingStrategy.EMBOSS;
        minimumAllowedExtentX                              : float                   = 12   * millimeter, 
        # used to enforce minimum interval between bits for ease of grabbing very small bits with fingers.

        minimumAllowedExtentY                              : float                   = 0    * millimeter,  
        minimumAllowedLabelToZMinOffset                    : float                   = 0    * millimeter,  
        minimumAllowedBoreToZMinOffset                     : float                   = 2    * millimeter, 
        enableExplicitLabelExtentX                         : bool                    = False,
        explicitLabelExtentX                               : float                   = 10    * millimeter,
        doLabelRetentionLip                                : bool                    = False, 
        directionsOfEdgesThatWeWillAddALabelRetentionLipTo : Sequence[NDArray]       = (xHat,),
    
        name                                               : Optional[str]  = None ,
    ):
        self.bit                                                 : Bit                  = (bit if bit is not None else Bit())
        self.bitHolder                                           : Optional[BitHolder]  = bitHolder
        self.angleOfElevation                                    : float                = angleOfElevation
        self.lecternAngle                                        : float                = lecternAngle
        self.lecternMarginBelowBore                              : float                = lecternMarginBelowBore
        self.lecternMarginAboveBore                              : float                = lecternMarginAboveBore
        self.boreDiameterAllowance                               : float                = boreDiameterAllowance
        self.mouthFilletRadius                                   : float                = mouthFilletRadius

        self.explicitBitProtrusion                               : float                = explicitBitProtrusion
        self.explicitBitEmbedment                                : float                = explicitBitEmbedment
        self.bitProtrusionStrategy                               : ProtrusionStrategy   = bitProtrusionStrategy

        self.labelExtentZ                                        : float       = labelExtentZ
        self.labelThickness                                      : float       = labelThickness
        self.labelZMax                                           : float       = labelZMax
        self.labelFontHeight                                     : float       = labelFontHeight
        self.labelFontName                                       : str         = labelFontName
        self.labelSculptingStrategy                              : float       = labelSculptingStrategy
        self.minimumAllowedExtentX                               : float       = minimumAllowedExtentX
        self.minimumAllowedExtentY                               : float       = minimumAllowedExtentY
        self.minimumAllowedLabelToZMinOffset                     : float       = minimumAllowedLabelToZMinOffset
        self.minimumAllowedBoreToZMinOffset                      : float       = minimumAllowedBoreToZMinOffset
        self.enableExplicitLabelExtentX                          : bool        = enableExplicitLabelExtentX
        self.explicitLabelExtentX                                : float       = explicitLabelExtentX
        self.doLabelRetentionLip                                 : bool        = doLabelRetentionLip 
        self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo  : Sequence[NDArray]    = directionsOfEdgesThatWeWillAddALabelRetentionLipTo
        
           
        
        # doLabelRetentionLip only makes sense in the case where we are using the
        # "floodWithInk" label text mechanism to generate a rectangular pocket
        # (intended to hold a printed paper card).  
        # In that case, we can sweep a "retention lip" profile around (some of)
        # the edges of the pocket that the edges of the paper card can be tucked
        # under to hold the card in place.
    
        # self.labelRetentionLipProfile = [
        #     np.array((zeroLength, zeroLength)),
        #     np.array((0.2*millimeter, zeroLength)),
        #     np.array((zeroLength, -0.07*millimeter))
        # ]
    

        # we will not add a lip to all edges.  Rather, we will add a lip only to
        # edges that are parallel (possibly within some tolerance) (or
        # anti-parallel) to any of the specified directions.  (this is geared toward
        # the cases where edges are straight lines.)
    
    
        # //test case:
        # // self.labelRetentionLipProfile = [
        # //     np.array((zeroLength, 0.1*millimeter)),
        # //     np.array((0.2*millimeter, 0.1*millimeter)),
        # //     np.array((0.2*millimeter, 0.3*millimeter)),
        # //     np.array((0.4*millimeter, 0.3*millimeter)),
        # //     np.array((0.2*millimeter, zeroLength)),
        # //     np.array((zeroLength, -0.07*millimeter))
        # // ];
        a = 0.4*millimeter
        b = 0.4*millimeter
        c = 0.03*millimeter

        #just for debugging, scale way down:
        # a*=0.1
        # b*=0.1
        # c*=0.1

        self.labelRetentionLipProfile = [
            np.array((zeroLength, zeroLength)),
            np.array((a, zeroLength)),
            np.array((a, -b + c)),
            np.array((zeroLength, -b))
        ]
        # This is a list of 2dPointVector describing the polygonal cross-section of
        # the labelRetentionLip.  The positive Y direction points out of the pocket.
        # The origin is on the upper edge of the side-wall of the pocket.  
        # the X direction is perpendicular to that edge.  positive X points "off the
        # edge of the cliff".

        # as a side effect of the above, 
        # self.bitHolder will be set to dummyBitHolder.

        # super().__init__(
        #     *self._build(),
        #     component = None, 
        #     name = name
        # )

        super().__init__(name)

    def _copy_to(self, copy: 'BitHolderSegment', copy_children: bool) -> None:
        copy.bit                                                 =   self.bit                                                 
        copy.bitHolder                                           =   None                                           
        copy.angleOfElevation                                    =   self.angleOfElevation                                    
        copy.lecternAngle                                        =   self.lecternAngle                                        
        copy.lecternMarginBelowBore                              =   self.lecternMarginBelowBore                              
        copy.lecternMarginAboveBore                              =   self.lecternMarginAboveBore                              
        copy.boreDiameterAllowance                               =   self.boreDiameterAllowance                               
        copy.mouthFilletRadius                                   =   self.mouthFilletRadius                                   

        copy.explicitBitProtrusion                               =   self.explicitBitProtrusion                               
        copy.explicitBitEmbedment                                =   self.explicitBitEmbedment                                
        copy.bitProtrusionStrategy                               =   self.bitProtrusionStrategy                               

        copy.labelExtentZ                                        =   self.labelExtentZ                                        
        copy.labelThickness                                      =   self.labelThickness                                      
        copy.labelZMax                                           =   self.labelZMax                                           
        copy.labelFontHeight                                     =   self.labelFontHeight                                     
        copy.labelFontName                                       =   self.labelFontName                                       
        copy.labelSculptingStrategy                              =   self.labelSculptingStrategy                              
        copy.minimumAllowedExtentX                               =   self.minimumAllowedExtentX                               
        copy.minimumAllowedExtentY                               =   self.minimumAllowedExtentY                               
        copy.minimumAllowedLabelToZMinOffset                     =   self.minimumAllowedLabelToZMinOffset                     
        copy.minimumAllowedBoreToZMinOffset                      =   self.minimumAllowedBoreToZMinOffset                      
        copy.enableExplicitLabelExtentX                          =   self.enableExplicitLabelExtentX                          
        copy.explicitLabelExtentX                                =   self.explicitLabelExtentX                                
        copy.doLabelRetentionLip                                 =   self.doLabelRetentionLip                                 
        copy.directionsOfEdgesThatWeWillAddALabelRetentionLipTo  =   self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo  

    def copyWithModification(self,
        bit                                                : Optional[Bit]                     = None,
        bitHolder                                          : Optional['BitHolder']             = None,
        angleOfElevation                                   : Optional[float]                   = None,
        lecternAngle                                       : Optional[float]                   = None,
        lecternMarginBelowBore                             : Optional[float]                   = None,
        lecternMarginAboveBore                             : Optional[float]                   = None,
        boreDiameterAllowance                              : Optional[float]                   = None,
        mouthFilletRadius                                  : Optional[float]                   = None,

        explicitBitProtrusion                              : Optional[float]                   = None,
        explicitBitEmbedment                               : Optional[float]                   = None,
        bitProtrusionStrategy                              : Optional[ProtrusionStrategy]      = None,

        labelExtentZ                                       : Optional[float]                   = None,
        labelThickness                                     : Optional[float]                   = None,                 
        labelZMax                                          : Optional[float]                   = None,
        labelFontHeight                                    : Optional[float]                   = None,
        labelFontName                                      : Optional[str]                     = None,
        labelSculptingStrategy                             : Optional[LabelSculptingStrategy]  = None,
        minimumAllowedExtentX                              : Optional[float]                   = None,
        minimumAllowedExtentY                              : Optional[float]                   = None,
        minimumAllowedLabelToZMinOffset                    : Optional[float]                   = None,
        minimumAllowedBoreToZMinOffset                     : Optional[float]                   = None,
        enableExplicitLabelExtentX                         : Optional[bool]                    = None,
        explicitLabelExtentX                               : Optional[float]                   = None,
        doLabelRetentionLip                                : Optional[bool]                    = None,
        directionsOfEdgesThatWeWillAddALabelRetentionLipTo : Optional[Sequence[NDArray]]       = None,
        name                                               : Optional[str]                     = None,
    ) -> 'BitHolderSegment':
        """ creates a new BitHolderSegment that has the same parameters as self, except for the specified new parameter values """
        return BitHolderSegment(
            bit                                                = bit                                                or self.bit                                                ,
            bitHolder                                          = bitHolder                                          or self.bitHolder                                          ,
            # bitHolder                                          = bitHolder                                          or None                                                    ,
            angleOfElevation                                   = angleOfElevation                                   or self.angleOfElevation                                   ,
            lecternAngle                                       = lecternAngle                                       or self.lecternAngle                                       ,
            lecternMarginBelowBore                             = lecternMarginBelowBore                             or self.lecternMarginBelowBore                             ,
            lecternMarginAboveBore                             = lecternMarginAboveBore                             or self.lecternMarginAboveBore                             ,
            boreDiameterAllowance                              = boreDiameterAllowance                              or self.boreDiameterAllowance                              ,
            mouthFilletRadius                                  = mouthFilletRadius                                  or self.mouthFilletRadius                                  ,
            
            explicitBitProtrusion                              = explicitBitProtrusion                              or self.explicitBitProtrusion                              ,
            explicitBitEmbedment                               = explicitBitEmbedment                               or self.explicitBitEmbedment                               ,
            bitProtrusionStrategy                              = bitProtrusionStrategy                              or self.bitProtrusionStrategy                              ,
            
            labelExtentZ                                       = labelExtentZ                                       or self.labelExtentZ                                       ,
            labelThickness                                     = labelThickness                                     or self.labelThickness                                     ,
            labelZMax                                          = labelZMax                                          or self.labelZMax                                          ,
            labelFontHeight                                    = labelFontHeight                                    or self.labelFontHeight                                    ,
            labelFontName                                      = labelFontName                                      or self.labelFontName                                      ,
            labelSculptingStrategy                             = labelSculptingStrategy                             or self.labelSculptingStrategy                             ,
            minimumAllowedExtentX                              = minimumAllowedExtentX                              or self.minimumAllowedExtentX                              ,
            minimumAllowedExtentY                              = minimumAllowedExtentY                              or self.minimumAllowedExtentY                              ,
            minimumAllowedLabelToZMinOffset                    = minimumAllowedLabelToZMinOffset                    or self.minimumAllowedLabelToZMinOffset                    ,
            minimumAllowedBoreToZMinOffset                     = minimumAllowedBoreToZMinOffset                     or self.minimumAllowedBoreToZMinOffset                     ,
            enableExplicitLabelExtentX                         = enableExplicitLabelExtentX                         or self.enableExplicitLabelExtentX                         ,
            explicitLabelExtentX                               = explicitLabelExtentX                               or self.explicitLabelExtentX                               ,
            doLabelRetentionLip                                = doLabelRetentionLip                                or self.doLabelRetentionLip                                ,
            directionsOfEdgesThatWeWillAddALabelRetentionLipTo = directionsOfEdgesThatWeWillAddALabelRetentionLipTo or self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo ,
            name                                               = name                                               or self.name                                               ,
        )

    @property
    def zMax(self):
        #   return
        #         max(
        #             10 * millimeter,
        #             # self.boreDiameter/cos(self.angleOfElevation) + self.mouthFilletRadius + 1.1 * millimeter
        #             dot(self.lecternTopPoint, zHat)
        #         );
        return self.lecternTopPoint @ zHat

    @property
    def boreDepth(self):
        # return 14 * millimeter; 
        return self.bit.length - self.bitProtrusion
  
    @property
    def zMin(self):
        return min(
            (
                zHat
                @ ( 
                    self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, 90 * degree) @ self.boreDirection)
                )
            ) - self.minimumAllowedBoreToZMinOffset,
            self.labelZMin - self.minimumAllowedLabelToZMinOffset
        )

    @property
    def extentX(self):
        return max([
                self.minimumAllowedExtentX,
                self.boreDiameter + 2*self.mouthFilletRadius + 0.2 * millimeter,
                self.boreDiameter + 2 * millimeter
            ])

    @property
    def extentY(self):
        return max(
            map(
                lambda x: max(
                    x.minimumAllowedExtentY,
                    (x.bitHolder.minimumAllowedExtentY if x.bitHolder else zeroLength),
                    (
                        x.bitHolder.mountHoleSpec.minimumAllowedClampingThickness
                        + x.bitHolder.mountHoleSpec.headClearanceHeight
                        if x.bitHolder
                        else zeroLength
                    )
                    + (
                        yHat
                        @ (
                            x.boreBottomCenter + x.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ x.boreDirection)
                        )
                    )  
                ),
                ( self.bitHolder.segments if self.bitHolder else (self,) )
            )
        )

        
    @property
    def labelExtentX(self):
        if self.enableExplicitLabelExtentX:
            return self.explicitLabelExtentX
        else:
            return self.extentX - 0.4 * millimeter

    # @labelExtentX.setter   
    # #it would probably be better not to be so clever about the way to override the default-computed labelExtentX:
    # # Rather than have a setter with side effects, we should have the user deal directly with explicitLabelExtentX 
    # # and a flag that controls whether the override applies.     
    # def labelExtentX(self, x): 
    #     self.explicitLabelExtentX = x   

    @property
    def labelText(self):
        return self.bit.labelText # "\u0298" is a unicode character that, at least in the Tinos font, consists of a circle, like an 'O', and a central isolated dot.  This character does not extrude correctly (the middle dot is missng)

    @property
    def labelZMin(self):
        return self.labelZMax  - self.labelExtentZ

    @property
    def labelXMin(self): return -self.labelExtentX/2

    @property
    def labelXMax(self):  return  self.labelExtentX/2

    @property
    def labelExtentY(self): return self.labelThickness

    @property
    def labelYMin(self):
        return (0 if self.labelSculptingStrategy == LabelSculptingStrategy.ENGRAVE else -1) * self.labelExtentY 

    @property
    def labelYMax(self): return self.labelYMin + self.labelExtentY
    
    @property
    def yMin(self): return zeroLength

    @property
    def yMax(self): return self.extentY
    
    @property
    def xMin(self): return -self.extentX/2

    @property
    def xMax(self): return self.extentX/2

    @property
    def origin(self): return np.array((0,0,0))
    
    @property
    def boreDirection(self):
        return rotationMatrix3d(xHat, -self.angleOfElevation) @ -yHat  #shooting out of the bore

    @property
    def boreDiameter(self):
        return self.bit.outerDiameter + self.boreDiameterAllowance
        
    @property
    def boreTopCenter(self):
        # //return 
        #     // vector(0, -1, tan(self.angleOfElevation))*self.bitProtrusionY
        #     // + self.boreDiameter/2 * (rotationMatrix3d(xHat,-90*degree)@self.boreDirection);
        return self.boreBottomCenter + 1 * meter * self.boreDirection

    @property
    def bitProtrusion(self) -> float:
        return (
            self.explicitBitProtrusion 
            if self.bitProtrusionStrategy == ProtrusionStrategy.explicitProtrusion
            else self.bit.length - self.explicitBitEmbedment
        ) 

    @property
    def lecternNormal(self):
        return rotationMatrix3d(xHat, -self.lecternAngle) @ -yHat
        
    @property
    def boreBottomCenter(self):
        # return self.boreTopCenter - self.boreDirection * self.bit.length;
        return self.borePiercePoint - self.boreDepth * self.boreDirection

    @property
    def bottomBoreCorner(self):
        return (
            self.origin - (rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal)
            * self.lecternMarginBelowBore
        )
                
    @property
    def borePiercePoint(self):
        # // return
        # //     self.origin + 
        # //     vector(0, sin(self.lecternAngle), cos(self.lecternAngle)) 
        # //     * (
        # //         self.lecternMarginBelowBore 
        # //         + (1/2) * 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
        # //     );
            
        return (
            self.origin - 
            (rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal)
            * (
                self.lecternMarginBelowBore
                + (1/2) * 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
            )
        )

    @property
    def topBoreCorner(self):
        return (
            self.origin - 
            (rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal)
            * (
                self.lecternMarginBelowBore
                + 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
            )
        )

    @property
    def lecternTopPoint(self):
        return (
            self.origin - 
            (rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal)
            * (
                self.lecternMarginBelowBore
                + 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
                + self.lecternMarginAboveBore
            )
        )
    
    @property
    def bottomPointOfMouthFilletSweepPath(self):
        return (
            self.bottomBoreCorner + 
            1/sin((90*degree - self.angleOfElevation + self.lecternAngle )/2) * self.mouthFilletRadius
            * normalize(
                mean(
                    rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal,
                    -self.boreDirection
                )
            )
        )

    # // @property
        # def topPointOfMouthFilletSweepPath(self)
        # //     function()
        # //     {
        # //         return 
        # //             self.bottomBoreCorner + 
        # //             1/sin((90*degree - self.angleOfElevation + self.lecternAngle )/2) * self.mouthFilletRadius
        # //             * normalize(
        # //                 mean(
        # //                     rotationMatrix3d(xHat, 90*degree) @ self.lecternNormal,
        # //                     -self.boreDirection
        # //                 )
        # //             );
        # //     };
        
    @property
    def bottomSaddlePointOfMouthFillet(self): #//see neil-4936          
        return self.bottomPointOfMouthFilletSweepPath + self.mouthFilletRadius * zHat

    def _raw_bodies(self) -> Iterable[adsk.fusion.BRepBody]:
        returnValue : list[adsk.fusion.BRepBody] = []
        colorCycleForHighlighting = highlight.getColorCycle()
        
        polygonVertices = [
                vector(self.xMin, self.yMin, zeroLength),
                vector(self.xMin, self.yMin + tan(self.lecternAngle) * self.zMax , self.zMax),
                vector(self.xMin, self.yMax, self.zMax),
                vector(self.xMin, self.yMax, self.zMin),
                vector(self.xMin, self.yMin, self.zMin),

                #vector(self.xMin, self.yMin, zeroLength), 
                #
                # do we need to repeat the initial point? no, and evidently, we
                # mustn't repeat the initial point.  This might differ from the
                # behavior of my OnShape function "createRightPolygonalPrism",
                # which I think I would have made tolerant of a repeated final
                # point.
            ]
        
        polygonVertices.reverse()
        # the order of the vertices determines the direction of the face, which
        # in turn determines the direction of the Extrude. I would prefer to
        # describe the extrude by giving a start point and an endpoint, but
        # there is not at present a pre-existing function to do this.

        # print(polygonVertices)
        # highlight.highlight(
        #     itertools.starmap(
        #         adsk.core.Point3D.create,
        #         polygonVertices
        #     )
        # )

        polygon = fscad.Polygon(
            *itertools.starmap(
                adsk.core.Point3D.create,
                polygonVertices
            )
        )
        # highlight.highlight(polygon)
        mainPrivateComponent : fscad.Component
        mainPrivateComponent : fscad.Component = fscad.Extrude(polygon, height=self.extentX)
        mainPrivateComponent.name = 'mainPrivateComponent'
        #the name is just for debugging

        boreTool = cylinderByStartEndRadius(startPoint=castToPoint3D(self.boreBottomCenter), endPoint=castToPoint3D(self.boreBottomCenter + 1*meter * self.boreDirection), radius = self.boreDiameter/2)
        # highlight.highlight(boreTool)
        boxOccurrence = mainPrivateComponent.create_occurrence()
        boxBody = boxOccurrence.bRepBodies.item(0)
        boreToolOccurrence = boreTool.create_occurrence()
        boreToolBody = boreToolOccurrence.bRepBodies.item(0)

        initialEntityTokensOfBox = captureEntityTokens(boxOccurrence)
        initialEntityTokensOfBoreTool = captureEntityTokens(boreToolOccurrence)

        combineFeatureInput = rootComponent().features.combineFeatures.createInput(targetBody=boxBody, toolBodies=fscad._collection_of((boreToolBody,)))
        combineFeatureInput.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        combineFeature = rootComponent().features.combineFeatures.add(combineFeatureInput)

        finalEntityTokensOfBox = captureEntityTokens(boxOccurrence)
        finalEntityTokensOfBoreTool = captureEntityTokens(boreToolOccurrence)
        

        edgesDescendedFromInitialEdges = [
            entity 
            for item in initialEntityTokensOfBox['bodies']
            for initialEdgeEntityToken in item['edges']
            for entity in design().findEntityByToken(initialEdgeEntityToken)
        ]
        # we have to be a bit careful when speaking about the identity of BRep
         # entities across operations.  From an intuitive point of view, we want
         # to talk about "an edge" which existed before the operation, and
         # continues to exist after the operation. However, we cannot trust that
         # the equality operator acting on BRepEdge objects will represent the
         # intuitive sense of identity.  If I were to call this list
         # "initialEdges", it would be unclear whether I were talking about the
         # collection of edge objects that I might have obtained by storing the
         # members of boxBody.edges before performing the operation, or whether I
         # am talking about the adge objects belonging to the current incarnation
         # of boxBody, which are "the same", in the intuitive sense" as the edge
         # objects that existed before the operation.  In fact, my meaning is the
         # latter.  Therefore, I call this variable
         # 'edgesDescendedFromInitialEdges'.

        facesDescendedFromInitialFaces = [
            entity 
            for item in initialEntityTokensOfBox['bodies']
            for initialFaceEntityToken in item['faces']
            for entity in design().findEntityByToken(initialFaceEntityToken)
        ]

        edgesUsedByFacesDescendedFromIntialFaces = [
            edge 
            for face in facesDescendedFromInitialFaces
            for edge in face.edges
        ]

        edgesOfInterest = [
            edge
            for edge in edgesUsedByFacesDescendedFromIntialFaces
            if edge not in edgesDescendedFromInitialEdges
        ]
        boreToolOccurrence.deleteMe()
        # highlight.highlight(edgesOfInterest)
        # print('len(edgesOfInterest): ' + str(len(edgesOfInterest)))
        
        filletFeatureInput = boxOccurrence.component.features.filletFeatures.createInput()

        filletFeatureInput.addConstantRadiusEdgeSet(
            edges= fscad._collection_of(edgesOfInterest),
            radius= adsk.core.ValueInput.createByReal(self.mouthFilletRadius),
            isTangentChain=False
        )

        filletFeature = boxOccurrence.component.features.filletFeatures.add(filletFeatureInput)
        
        # mainPrivateComponent = fscad.BRepComponent(*boxOccurrence.bRepBodies)

        # returnValue += [
        #     fscad.brep().copy(x)
        #     for x in boxOccurrence.bRepBodies
        # ]
        # it is probably somewhat inefficient to copy the bodies here, because they will just be fed into the constructor for BRepComponent, which will copy them again.
        # Ideally, I would leave the temporary boxOccurence in place until I had called the BRepComponent constructor, and then delete the temporary occurence.

        # boxOccurrence.deleteMe()
        # returnValue += [
        #     x.brep 
        #     for x in TextRow(
        #         fontName="Times New Roman",
        #         text="Abc"
        #     ).bodies
        # ]




        labelGalley = Galley(
            fontName=self.labelFontName,
            text=self.labelText,
            width = self.labelExtentX,
            height = self.labelExtentZ,
            rowSpacing = 1.3,
            rowHeight =  self.labelFontHeight,
            horizontalAlignment = HorizontalAlignment.CENTER,
            verticalAlignment = VerticalAlignment.TOP,
            clipping=True,
            leftMargin=zeroLength,
            rightMargin=zeroLength,
            topMargin=zeroLength,
            bottomMargin=zeroLength
        )



        labelGalley.transform(rigidTransform3D(
            origin = adsk.core.Point3D.create(self.labelXMin, self.labelYMin, self.labelZMin),
            xDirection  = xHat,
            zDirection  = -yHat
        ))

        
        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in myGalley.bodies
        # ]


        #extrude myGalley to form labelSculptingTool
        # labelSculptingTool = fscad.Extrude(myGalley, self.labelThickness)
        

        # in the case where len(myGalley.bodies) == 0 (which happens, for instance, when 
        # labelText is an empty string or a string containing only whitepsace),
        # the above fscad.Extrude operation throws an exception saying "can't extrude non-planer geometry with Extrude".
        # I would propose modifying fscad.Extrude to be tolerant of the case of extruding an empty component.
        # True, the empty component is not planar, but it can certainly be extruded - the result is trivial -- namely no bodies.
        # Come on people; zero exists.

        labelSculptingTool = (
            fscad.Extrude(labelGalley, -self.labelThickness)
            # I would like to be able to specify or hint at an extrude direction, or specify
            # start and end points, rather than relying on the vagueries of the face direction
            # (which at least are consistent and predictable here -- actually they are not consistent
            # the filled rectangle seems to point in a different direction from the text.).
            # TODO, within Galley._build, ensure that the rect points up.  I suspect that, at the moment it points down.
            # (or maybe the problem is with getAllSheetBodiesFromSketch returning faces whose normal is 
            # pointing counter to the sketch's normal -- yes I suspect that is the problem.
            if len(labelGalley.bodies) > 0
            else fscad.BRepComponent() # this is simply an empty component.
        )
        labelSculptingTool.name = 'labelSculptingTool'
        # the name is only used a s a sanity check during debugging

        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in labelSculptingTool.bodies
        # ]

        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in myGalley.bodies
        # ]

        # // sculpt (i.e. either emboss or engrave, according to self.labelSculptingStrategy) the label tool onto the main body.

        # if self.labelSculptingStrategy == LabelSculptingStrategy.EMBOSS:
        #     mainPrivateComponent = fscad.Union(mainPrivateComponent, labelSculptingTool)
        # elif self.labelSculptingStrategy == LabelSculptingStrategy.ENGRAVE:
        #     mainPrivateComponent = fscad.Difference(mainPrivateComponent, labelSculptingTool)
        
        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in mainPrivateComponent.bodies
        # ]
        
        boxBody = boxOccurrence.bRepBodies.item(0)
        labelSculptingToolOccurrence = labelSculptingTool.create_occurrence()
        labelSculptingToolBodies = labelSculptingToolOccurrence.bRepBodies

        initialEntityTokensOfBox = captureEntityTokens(boxOccurrence)
        initialEntityTokensOfLabelSculptingTool = captureEntityTokens(labelSculptingToolOccurrence)
        
        combineFeatureInput = rootComponent().features.combineFeatures.createInput(targetBody=boxBody, toolBodies=fscad._collection_of(labelSculptingToolOccurrence.bRepBodies))
        combineFeatureInput.operation = (adsk.fusion.FeatureOperations.JoinFeatureOperation if self.labelSculptingStrategy == LabelSculptingStrategy.EMBOSS else adsk.fusion.FeatureOperations.CutFeatureOperation)
        combineFeature = rootComponent().features.combineFeatures.add(combineFeatureInput)

        finalEntityTokensOfBox = captureEntityTokens(boxOccurrence)
        finalEntityTokensOfLabelSculptingTool = captureEntityTokens(labelSculptingToolOccurrence)
        

        edgesDescendedFromInitialEdges = [
            entity 
            for item in initialEntityTokensOfBox['bodies']
            for initialEdgeEntityToken in item['edges']
            for entity in design().findEntityByToken(initialEdgeEntityToken)
        ]


        facesDescendedFromInitialFaces = [
            entity 
            for item in initialEntityTokensOfBox['bodies']
            for initialFaceEntityToken in item['faces']
            for entity in design().findEntityByToken(initialFaceEntityToken)
        ]

        edgesUsedByFacesDescendedFromIntialFaces = [
            edge 
            for face in facesDescendedFromInitialFaces
            for edge in face.edges
        ]

        edgesOfInterest = [
            edge
            for edge in edgesUsedByFacesDescendedFromIntialFaces
            if edge not in edgesDescendedFromInitialEdges
        ]
        labelSculptingToolOccurrence.deleteMe()
        # highlight.highlight(edgesOfInterest)
        # print('len(edgesOfInterest): ' + str(len(edgesOfInterest)))
        # mainPrivateComponent = fscad.BRepComponent(*boxOccurrence.bRepBodies)
        # print('mainPrivateComponent.name: ' +  mainPrivateComponent.name)

        sweepingEdgeCandidates = edgesOfInterest

        # returnValue += [fscad.brep().copy(x) for x in boxOccurrence.bRepBodies]; boxOccurrence.deleteMe()

        doHighlighting = False
        if self.doLabelRetentionLip:
            # doLabelRetentionLip is intended to be used only in the case where self.labelSculptingStrategy == LabelSculptingStrategy.ENGRAVE
            # and where the label sculpting operation created a big rectangular pocket (e.g. the labelText contained the \floodWithInk directive).

            # identify the edges that we want to sweep the lip profile along.
            #     //the edges that we might want to sweep along are the set of edges e such that:
            #     // 1) e was created by the labelSculpting operation 
            #     // and 2) e bounds a face that existed before the label sculpting operation (i.e. a face that the labelSculpting operation modified but did not create.)
            #     // another way to state condition 2 is: e bounds a face that was not created by the label sculpting region.
            #     // another way to state condition 2 is: there exists a face not created by the label sculpting operation that owns e
            
            



            # figure out which of the sweepingEdgeCandidates are aligned with any of the self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo
            
            def isAlignedWithAnyOfDirectionsOfEdgesThatWeWillAddALabelRetentionLipTo(candidateEdge: adsk.fusion.BRepEdge) -> bool:
                testDirection : NDArray
                for testDirection in self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo:
                    # return true if the candidateEdge (or, for our purposes, the tangent direction of the edge at some arbitrary point on the edge (because our
                    # application is geared toward the candidateEdges being straight lines)) is aligned with (i.e. parallel or anti-parallel to) testDirection
                    edgeTangentDirection = candidateEdge.evaluator.getTangent(candidateEdge.evaluator.getParameterExtents()[1])[1]
                    # what is the difference between
                    # CurveEvaluator3D::getTangent() and
                    # CurveEvaluator3D::getFirstDerivative() ?   Maybe tangent
                    # is normalized whereas first derivative has meaningful
                    # magnitude? 

                    if castToVector3D(testDirection).isParallelTo(edgeTangentDirection):
                        return True

                    # adsk.core.Vector3D::isParallelTo() seems to return true in both the parallel and the anti-parallel case --
                    # I don't like this definition personally, but in our case here that is the desired behavior.
                    # (i.e. we want to pick out the edges that are parallel or anti-parallel to the testDirection).
                return False

            sweepingEdges = list(
                filter(
                    isAlignedWithAnyOfDirectionsOfEdgesThatWeWillAddALabelRetentionLipTo,
                    sweepingEdgeCandidates
                )
            )

            # sweepingPaths = partitionEdgeSequenceIntoPaths(sweepingEdges)

            sweepingChains = partitionEdgeSequenceIntoChains(sweepingEdges)
            # for sweepingEdge in sweepingEdges:
            #     highlight.highlight(sweepingEdge, colorEffect=next(colorCycleForHighlighting)['color'])


            # for sweepingPath in sweepingPaths:
            #     highlight.highlight(sweepingPath, colorEffect=next(colorCycleForHighlighting)['color'])


            # we might also consider filtering on the whether
            # candidateEdge.geometry.curveType ==
            # adsk.core.Curve3DTypes.Line3DCurveType , which I think would
            # select all the straight line edges (and only those edges). we want
            # to iterate over all connected chains of edges that exist within
            # the set of sweepingEdges. for each connected chain, we will sweep
            # a lip. 

            # we want a coordinate system whose y axis points "up" out of the pocket. 
            # whose z axis is along (tangent or anti-tangent) to the edge, directed in such a way so 
            # that the x axis points "off the edge of the cliff"
            # and whose origin is on the edge

            #          y
            #          ^
            #          |
            #          |--> x
            #
            # _________. (0,0)          ________________
            #          |               |
            #          |   ( pocket )  |
            #          |_______________|

            lipProfile = fscad.Polygon(*map(castToPoint3D, self.labelRetentionLipProfile), name='lipProfile')
            # highlight.highlight(lipProfile, colorEffect=next(colorCycleForHighlighting)['color'])

            lipBodies : Sequence[adsk.fusion.BRepBodies] = []
            
            # for sweepingChain in sweepingChains:
            for i in range(len(sweepingChains)):
                sweepingChain = sweepingChains[i]
                # highlight.highlight(sweepingPath, colorEffect=next(colorCycleForHighlighting)['color'])
                if doHighlighting:
                    colorEffectForHighlighting = next(colorCycleForHighlighting)['color']
                    customGraphicsGroupToReceiveTheCustomGraphics=fscad.BRepComponent(name='highlight').create_occurrence().component.customGraphicsGroups.add()
                sweepingPath = adsk.fusion.Path.create(
                    curves=fscad._collection_of(sweepingChain), 
                    chainOptions=adsk.fusion.ChainedCurveOptions.noChainedCurves
                    # the chainOptions argument tells fusion whether to try to find add add to the path edges or sketch curves other than those specified in curves. 
                    # we are telling fusion not to try to find more edges than those we havve (carefully) specified.
                )

                # sweepingPath = boxOccurrence.component.features.createPath(
                #     curve=fscad._collection_of(sweepingChain),
                #     isChain = False
                # )
                
                if doHighlighting:
                    highlight.highlight(sweepingPath, 
                        colorEffect=colorEffectForHighlighting, 
                        customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics
                    )

                sampleEdge = sweepingPath.item(0).entity
                assert isinstance(sampleEdge, adsk.fusion.BRepEdge)
                # sampleEdge is any arbitrary edge in the path.  We will use sampleEdge to
                # place our profile so that it is suitable for sweeping along sweepingPath.

                # the hostFace is the face into which the pocket was cut.
                # we can get the host face by finding the member of facesDescendedFromInitialFaces that has sampleEdge
                # in one of its loops.  I think that there will always be exactly one such face.
                
                # print("len(sampleEdge.faces): " + str(len(sampleEdge.faces)))

                candidateHostFaces = tuple( 
                    face for
                    face in sampleEdge.faces 
                    if  face in facesDescendedFromInitialFaces
                )
                # assert len(candidateHostFaces) == 1
                hostFace : adsk.fusion.BRepFace = candidateHostFaces[0]

                # sampleCoEdge is the coedge whose edge is sampleEdge, and whose loop whose parent face is hostFace.
                sampleCoEdge : adsk.fusion.BRepCoEdge = tuple(
                    coEdge
                    for coEdge in sampleEdge.coEdges
                    if coEdge.loop.face == hostFace
                )[0]

                # I trust that, whereas the sense of direction along sampleEdge is arbitrary, 
                # the sense of direction along sampleCoEdge is such that, if we were to walk
                # along sampleCoEdge in the increasing-parameter direction, with up being the normal of hostFace,
                # hostFace would be on our left.

                doHighlightHostFace = False
                if doHighlighting and doHighlightHostFace:
                    highlight.highlight(hostFace, 
                        colorEffect=colorEffectForHighlighting,
                        customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics
                    )

                #var yDirection = -yHat In our case, we have constructed things
                # above so that we know that the normal of the host facce is
                # -yHat.  However, let's write this in a way that would work
                # generally:
                origin = sampleEdge.pointOnEdge
                # some (arbitrary) point along the
                # sampleEdge
                yDirection = hostFace.evaluator.getNormalAtPoint(origin)[1]
                # in the present application, hostface is always going to be
                # planar, so it doesn't really matter along the edge (or even
                # along the whole face) we evaluate the normal.
                zDirection = sampleEdge.evaluator.getTangent(sampleEdge.evaluator.getParameterAtPoint(origin)[1])[1]
                
                zDirection.scaleBy(
                      (-1 if sampleCoEdge.isOpposedToEdge else 1)
                    * (-1 if sampleEdge.isParamReversed else 1)
                    * -1
                )
                # zDirection is such that if we walk along sampleEdge in zDirection with hostFace normal being up,
                # the hostFace will be on our right.
                # print('zDirection: ' + str(zDirection.asArray()))
                
                t = rigidTransform3D(
                        origin = origin,
                        yDirection = yDirection,
                        zDirection = zDirection,
                    )

                # print("t.determinant: " + str(t.determinant))
                placedLipProfile = lipProfile.copy().transform(t)
                # placedLipProfile.name = 'placedLipProfile ' + str(i)
                # placedLipProfile.create_occurrence()

                # print('t' + str(i) + ': ' + str(t.asArray()))
                # print(str(i) + ': t.determinant: ' + str(t.determinant))
                # print(str(i) + ': xDirection.length: ' + str(xDirection.length))
                # print(str(i) + ': yDirection.length: ' + str(yDirection.length))
                # print(str(i) + ': zDirection.length: ' + str(zDirection.length))


                if doHighlighting:
                    highlight.highlight(placedLipProfile, 
                        colorEffect=colorEffectForHighlighting,
                        customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics
                    )



                # sweepFeatureInput = boxOccurrence.component.features.sweepFeatures.createInput(
                #     profile= fscad._collection_of(tuple(
                #         fscadFace.brep
                #         for fscadFace in placedLipProfile.faces
                #     )),
                #     path = sweepingPath,
                #     operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                # )


                # sweepFeature = boxOccurrence.component.features.sweepFeatures.add(sweepFeatureInput)

                lip = fscad.Sweep(
                    entity=placedLipProfile, 
                    path = tuple(
                        pathEntity.curve
                        for pathEntity in sweepingPath
                    ), 
                    name='lip'
                )
                if doHighlighting:
                    highlight.highlight(lip, 
                        colorEffect=colorEffectForHighlighting,
                        customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics
                    )
                lipBodies += list(
                    body.brep for body in lip.bodies
                )

            
                

            lipTool = fscad.BRepComponent(*lipBodies, name='lipTool')
            lipToolOccurrence = lipTool.create_occurrence()

            combineFeatureInput = boxOccurrence.component.features.combineFeatures.createInput(
                targetBody=boxOccurrence.bRepBodies[0], 
                toolBodies=fscad._collection_of(lipToolOccurrence.bRepBodies)
            )
            combineFeatureInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            combineFeature = boxOccurrence.component.features.combineFeatures.add(combineFeatureInput)
            lipToolOccurrence.deleteMe()
            # var chainCandidates = connectedComponents(context,
            # sweepingEdges, AdjacencyType.VERTEX);

        returnValue += [fscad.brep().copy(x) for x in boxOccurrence.bRepBodies]; boxOccurrence.deleteMe()
        
        return returnValue


class MountHoleSpec :
    """ a MountHole (or, perhaps more correctly, specifications for a mount
    hole) to be contained within a BitHolder.   This construction of the bodies
    used in the creation of the mount hole is done by the user of this class.
    """ 

    def __init__(self,
        shankClearanceDiameter          : float = 3 * millimeter,
        headClearanceDiameter           : float = 8 * millimeter,
        headClearanceHeight             : float = 2.7 * millimeter,
        minimumAllowedClampingThickness : float = 1/4 * inch,
        clampingDiameter                : float = 5/8 * inch
    ):
        self.shankClearanceDiameter          : float = shankClearanceDiameter          
        self.headClearanceDiameter           : float = headClearanceDiameter           
        self.headClearanceHeight             : float = headClearanceHeight             
        self.minimumAllowedClampingThickness : float = minimumAllowedClampingThickness 
        self.clampingDiameter                : float = clampingDiameter                

    def cutIntoComponent(self, component : fscad.Component, 
        axis: adsk.core.InfiniteLine3D
    ) -> fscad.Component :
        # the direction of axis determines the direction along which we "drill"
        # First, we locate the counterBoreEndPoint by finding the maximum point
        # on the axis that is contained in any of the bodies of component, and
        # moving in the negative axis direction by a distance
        # self.minimumAllowedClampingThickness. We cut a hole of diameter
        # self.shankClearanceDiameter by extruding a disk of that diameter
        # starting from counterBoreEndPoint and moving in the positive axis
        # direction until we have cut through all bodies of the component. Then,
        # we cut a hole of diameter self.headClearanceDiameter by sweeping a
        # disk of that diameter starting from counterBoreEndPoint and moving in
        # the negative axis direction until we have cut through all bodies of
        # the component. we return a new component.
        offset = axis.direction.copy()
        offset.normalize()
        offset.scaleBy( - self.minimumAllowedClampingThickness )
        extremePoints = evExtremeSkewerPointsOfBodies(*(body.brep for body in component.bodies), axis=axis)
        
        if extremePoints:

            counterBoreEndPoint = extremePoints[1].copy()
            counterBoreEndPoint.translateBy(offset)
            # highlight.highlight(extremePoints[0], colorEffect='darkgreen')
            # highlight.highlight(extremePoints[1], colorEffect='darkorange')
            # highlight.highlight(counterBoreEndPoint, colorEffect='firebrick')

            tool = fscad.Union(
                cylinderByStartEndRadius(
                    radius = self.shankClearanceDiameter/2 , 
                    startPoint = counterBoreEndPoint, 
                    endPoint = castToPoint3D( castTo3dArray(counterBoreEndPoint) + 1*meter*castTo3dArray(axis.direction) )
                ),
                cylinderByStartEndRadius(
                    radius = self.headClearanceDiameter/2 , 
                    startPoint = counterBoreEndPoint, 
                    endPoint = castToPoint3D( castTo3dArray(counterBoreEndPoint) - 1*meter*castTo3dArray(axis.direction) )
                )
            )
            # highlight.highlight(tool, colorEffect='darkgreen')
            return fscad.Difference(component, tool)
            # TODO: the 1*meter, above, is a major hack that is intended to mean
            # "infinity".  We really ought to evaluate the bounding box of the
            # component and make sure that we have fully penetrated all the way
            # through the component.  
        else:
            # in this case, there were no skewer points, which most likely means that axis does 
            # not intersect the body. 
            return component
        


class BitHolder  (fscad.Component) :
    """ a BitHolder is a collection of BitHolderSegment objects along with some
    parameters that specify how the bitHolderSegments are to be welded together 
    to make a single BitHolder.     """

    def __init__(self,
            segments                    : Tuple[BitHolderSegment]              = tuple()                                                  ,
            mountHoleSpec               : 'MountHoleSpec'                      = MountHoleSpec(
                    #these clearance diameters are appropriate for a UTS 8-32 pan-head screw.
                    shankClearanceDiameter            = 4.4958 * millimeter,
                    headClearanceDiameter             = 8.6    * millimeter,
                    minimumAllowedClampingThickness   = 3      * millimeter,
                    clampingDiameter                  = 21     * millimeter,
                    headClearanceHeight               = 2.7    * millimeter,
                )                                                    ,
            minimumAllowedExtentY       : float                                = 12 * millimeter                                         ,
            mountHolesGridSpacing       : float                                = 1 * inch                                                ,
            explicitMountHolesPositionZ : float                                = zeroLength                                              ,
            mountHolesPositionZStrategy : MountHolesPositionZStrategy          = MountHolesPositionZStrategy.grazeBottomOfSaddleBoreLip  ,
            name                        : Optional[str]                        = None                                                    ,
        ):
        
        
        self.mountHoleSpec               : MountHoleSpec = mountHoleSpec
        self.minimumAllowedExtentY       : float = minimumAllowedExtentY
        self.mountHolesGridSpacing       : float = mountHolesGridSpacing
        # the mountHolesInterval will be constrained to be an integer multiple of this length.
        self.mountHolesPositionZStrategy : MountHolesPositionZStrategy = mountHolesPositionZStrategy
        self.explicitMountHolesPositionZ : float = explicitMountHolesPositionZ  
        self.segments                    : Tuple[BitHolderSegment] = segments
        # super().__init__(
        #     *self._build(),
        #     component = None, 
        #     name = name
        # )
        super().__init__(name)

    def _copy_to(self, copy: 'BitHolder', copy_children: bool) -> None:
        print(f"BitHolder::_copy_to() is running for the BitHolder named '{self.name}'.")
        copy.segments                     = (segment.copy() for segment in self.segments)
        copy.mountHoleSpec                = self.mountHoleSpec               
        copy.minimumAllowedExtentY        = self.minimumAllowedExtentY       
        copy.mountHolesGridSpacing        = self.mountHolesGridSpacing       
        copy.mountHolesPositionZStrategy  = self.mountHolesPositionZStrategy 
        copy.explicitMountHolesPositionZ  = self.explicitMountHolesPositionZ 

    @property        
    def xMinMountHolePositionX(self):
        return 0.5 * self.mountHolesGridSpacing - 1.5 * millimeter; 
    
    @property
    def mountHolePositions(self) -> Sequence[adsk.core.Point3D]:
        mountHolePositions = [None]*2      
        
        # compute mountHolesPositionZ
        if self.mountHolesPositionZStrategy == MountHolesPositionZStrategy.explicit:
            # strategy 1: hard coded value
            mountHolesPositionZ = self.explicitMountHolesPositionZ
        elif self.mountHolesPositionZStrategy == MountHolesPositionZStrategy.grazeBottomOfSaddleBoreLip:
            # strategy 2: grazing the bottom saddle of the bore lip
            mountHolesPositionZ = max(
                    map(
                        lambda x: zHat @ x.bottomSaddlePointOfMouthFillet,
                        self.segments
                    )
                ) + self.mountHoleSpec.headClearanceDiameter/2
        
        elif self.mountHolesPositionZStrategy == MountHolesPositionZStrategy.middle :
            # strategy 3: z midpoint
            mountHolesPositionZ = mean(self.zMin, self.zMax)
        else:
            mountHolesPositionZ = zeroLength
        
        # compute the x coordinates of the mount hole positions
        if self.extentX < self.mountHolesGridSpacing:
            return []
        

        mountHolesInterval =  floor(
                self.extentX - self.xMinMountHolePositionX - self.mountHoleSpec.clampingDiameter/2 , 
                self.mountHolesGridSpacing
            )            
        mountHolePositions[0] = (
                #self.extentX/2 - mountHolesInterval/2,
                self.xMinMountHolePositionX,
                zeroLength,
                mountHolesPositionZ
            )

        mountHolePositions[1] = mountHolePositions[0] + mountHolesInterval * xHat            
        return  tuple( map(castToPoint3D, mountHolePositions ))

    @property
    def extentX(self) -> float:
        return sum(
            map(
                lambda segment: segment.extentX,
                self.segments
            )
        )    
    
    @property
    def xMin(self) -> float:
        return zeroLength

    @property    
    def xMax(self) -> float:
        return self.xMin + self.extentX
    
    @property
    def zMax(self) -> float:
        return max(
            *map(
                lambda segment: segment.zMax,
                self.segments
            )
        )

    @property
    def zMin(self) -> float:
        return min(
            *map(
                lambda segment: segment.zMin,
                self.segments
            )
        )
    
    @property
    def extentZ(self) -> float:
        return self.zMax - self.zMin
    
    @property
    def yMin(self) -> float:
        return min(
            *map(
                lambda segment: segment.yMin,
                self.segments
            )
        )

    @property
    def yMax(self) -> float:
        return max(
            *map(
                lambda segment: segment.yMax,
                self.segments
            )
        )
    
    @property
    def extentY(self) -> float:
        return self.yMax - self.yMin

    @property
    def segments(self) -> Tuple[BitHolderSegment]:
        return self._segments
    
    @segments.setter
    def segments(self, newSegments : Tuple[BitHolderSegment]):
        self._segments = tuple(newSegments)
        # print(f"The BitHolder with name {self.name} has received {len(self._segments)} segments.")
        for segment in self._segments:
            segment.bitHolder = self

    # the fscad.Component::_cached_brep_bodies property and the method
    # fscad.Component::_get_cached_brep_bodies(), which uses the
    # _cached_brep_bodies property are geared towards caching the results of
    # transformations upon a component, NOT caching the (untransformed) bodies
    # generated by expensive Fusion operations.  The latter type of caching is
    # not implemented by fscad.Component (although it would be nice if such
    # behavior were built into fscad.Component, and have both types of caching
    # use potentially the same underlying cache -- fscad's MemoizeComponent
    # decorator acheives a similar goal, but at a different level.).  Rather,
    # fscad.Component leaves the caching of potentially-expensive
    # body-construction operations up to the subclass. One example, within
    # fscad, of a subclass of fscad.Component that does the latter type of
    # caching (i.e. caching the results of potentially-expensive fusion
    # body-construction operations (typically body construction operations that
    # cannot be done purely with the TemporyBrepManager, but for which a
    # temporary fusion component must be created.)) is the fscad.ExtrudeBase class.

    def _raw_bodies(self) -> Iterable[adsk.fusion.BRepBody]:
        print(f"BitHolder::_raw_bodies() is running for the BitHolder named '{self.name}'.")
        
        returnValue : list[adsk.fusion.BRepBody] = []
        insertionPoint = vector(self.xMin, zeroLength, zeroLength).astype(dtype = float)
        transformedSegments : list[fscad.Component] = []
        segment: BitHolderSegment
        for segment in self.segments:
            transformedSegments.append(segment.copyWithModification().translate(*(insertionPoint - segment.xMin * xHat)))
            insertionPoint += segment.extentX * xHat
        combinedSegments = fscad.Union(*transformedSegments)

        

        # highlight.highlight(self.mountHolePositions)

        for mountHolePosition in self.mountHolePositions:
            combinedSegments = self.mountHoleSpec.cutIntoComponent(component = combinedSegments, axis = adsk.core.InfiniteLine3D.create(origin = mountHolePosition, direction = castToVector3D(yHat)))

        returnValue = (x.brep for x in combinedSegments.bodies)

        return returnValue



class HorizontalAlignment(Enum):
    LEFT = enum.auto()
    CENTER = enum.auto()
    RIGHT = enum.auto()

class VerticalAlignment(Enum):
    TOP = enum.auto()
    CENTER = enum.auto()
    BOTTOM = enum.auto()

class GalleyAnchor_e(Enum):
    TOP_LEFT    = enum.auto();  TOP_CENTER    = enum.auto();  TOP_RIGHT    = enum.auto();
    CENTER_LEFT = enum.auto();  CENTER        = enum.auto();  CENTER_RIGHT = enum.auto();
    BOTTOM_LEFT = enum.auto();  BOTTOM_CENTER = enum.auto();  BOTTOM_RIGHT = enum.auto();

class Galley(fscad.BRepComponent):
    # I don't think I fully appreciate fscad's use of child components,
    # and fscad's convention that child components are optionally-displayable precursors of the component.  It might
    # make sense to have some of the defining geometry (like the rectangles that defines the outer borders, 
    # the margin borders, etc, and maybe the individual textRows as child components).

    # The Galley component reinvents a very tiny bit of TeX-like text layout functionality.
    # A more fully-featured version of Galley wouldn't bother with Fuasion sketch text and would instead
    #  actually invoke TeX under the hood (can pip install TeX?),
    #  but this is just a proof-of-concept / good-enough for the present application.

    def __init__(self, 
        width : float = 8.5 * inch,
        height: float = 11 * inch,
        clipping: bool = True,
        fontName: Union[str, Sequence[str]] = "Arial",
        rowHeight: Union[float, Sequence[float]] = 10/72 * inch,
        rowSpacing: Union[float, Sequence[float]] = 1,
        #this is a unitless ratio that sets the ratio of the vertical interval between successive textRows and the rowHeight
        horizontalAlignment : HorizontalAlignment = HorizontalAlignment.LEFT,
        verticalAlignment : VerticalAlignment = VerticalAlignment.TOP,
        
        leftMargin : float    = zeroLength,
        rightMargin : float   = zeroLength,
        topMargin : float     = zeroLength,
        bottomMargin : float  = zeroLength,
        text : str = "",
        name: str = None
    ):

        self._width  : float = width
        self._height : float = height
        self._clipping : bool = clipping
        self._fontName  = fontName
        self._rowHeight = rowHeight
        self._rowSpacing = rowSpacing

        self._fontNames : Tuple[str] = (fontName if not isinstance(fontName, str) else (fontName,))
        self._rowHeights : Tuple[float] = (rowHeight if isinstance(rowHeight, Sequence) else (rowHeight,))
        self._rowSpacings : Tuple[float] = (rowSpacing  if isinstance(rowSpacing, Sequence) else (rowSpacing,)) 

        self._horizontalAlignment : HorizontalAlignment = horizontalAlignment
        self._verticalAlignment : VerticalAlignment = verticalAlignment
        
        self._leftMargin : float    = leftMargin
        self._rightMargin : float   = rightMargin
        self._topMargin : float     = topMargin
        self._bottomMargin : float  = bottomMargin
        self._text : str = text


        super().__init__(
            *self._build(),
            component = None, 
            name = name
        )

    @property
    def width(self) -> float:
        return self._width  
    
    @property
    def height(self) -> float:
        return self._height
    
    @property
    def clipping(self) -> bool:
        return self._clipping
    
    @property
    def fontName(self) -> str:
        return self._fontName
    
    @property
    def rowHeight(self) -> float:
        return self._rowHeight

    @property
    def rowSpacing(self) -> float:
        return self._rowSpacing

    @property
    def horizontalAlignment(self) -> HorizontalAlignment:
        return self._horizontalAlignment

    @property
    def verticalAlignment(self) -> VerticalAlignment:
        return self._verticalAlignment

    @property
    def leftMargin(self) -> float:
        return self._leftMargin

    @property
    def rightMargin(self) -> float:
        return self._rightMargin

    @property
    def topMargin(self) -> float:
        return self._topMargin
    
    @property
    def bottomMargin(self) -> float:
        return self._bottomMargin
    
    @property
    def text(self) -> str:
        return self._text

    @property
    def fontNames(self) -> Tuple[str]:
        return self._fontNames

    @property
    def rowHeights(self) -> Tuple[float]:
        return self._rowHeights

    @property
    def rowSpacings(self) -> Tuple[float]:
        return self._rowSpacings

    @property
    def midPoint(self) -> adsk.core.Point3D:
        return adsk.core.Point3D.create(self.width/2, self.height/2, 0)

    def _build(self) -> Sequence[adsk.fusion.BRepBody]:
        returnValue : list[adsk.fusion.BRepBody] = []

        regExPatternForTexDirective = re.compile(r"\\(?P<controlWord>\w+)(\{(?P<argument>.*?)\}|)\b")
        texDirectives = [
            {
                'controlWord': match.group('controlWord'),
                'argument':  match.group('argument')
            }
            for match in regExPatternForTexDirective.finditer(self.text)
        ]
        sanitizedText = regExPatternForTexDirective.sub('',self.text)

        floodWithInk = any(
            map(
                lambda x: x['controlWord'] == 'floodWithInk',
                texDirectives
            )
        )

        #defining extentBox and marginBox are mainly meant for debugging,
        # and I need to figure out how to do this in a more fscad-like way.
        # need to figure out how fscad thinks about transforms (does fscad require/assume/enforce
        # that all fusion components are located at the origin of the world?)
        self.extentBox = fscad.Rect(self.width, self.height, 'extentBox')
        self.marginBox = rectByCorners(
            (self.leftMargin, self.bottomMargin),
            (self.width - self.rightMargin, self.height - self.topMargin),
            name='marginBox'
        )


        # highlight.highlight(fscad.Rect(self.width, self.height).edges)
        # highlight.highlight(
        #     rectByCorners(
        #         (self.leftMargin, self.bottomMargin),
        #         (self.width - self.rightMargin, self.height - self.topMargin)
        #     ).edges
        # )
        if floodWithInk:
            returnValue += [
                body.brep 
                for body in 
                # rectByCorners(
                #     corner1=vector(zeroLength, zeroLength, zeroLength),
                #     corner2=vector(self.width, self.height, zeroLength)
                # ).bodies
                self.extentBox.bodies
            ]
        else:
            linesOfText = sanitizedText.split("\n")
            # print('linesOfText: ' + str(linesOfText))
            initZ = zeroLength
            #// the entries in the self.rowSpacings affect how much space will
            # exist between a row and the row above it. (thus, row spacing for
            # the first row has no effect - only for rows after the first row.)
            
            # # //verticalRowInterval is the vertical distance that we will move the insertion point between successive rows.
            # # //var verticalRowInterval = self.rowHeight * self.rowSpacing; 
            
            
            # //heightOfAllText is the distance from the baseline of the bottom row to the ascent of the top row, when all rows are laid out.
            # //var heightOfAllText = verticalRowInterval * size(linesOfText);
            heightOfAllText = sum(
                (
                    self.rowSpacings[i % len(self.rowSpacings)]
                    if i > 0 else 1.0
                ) 
                * self.rowHeights[i % len(self.rowHeights)]
                for i in range(0, len(linesOfText))
            )


            if  self.horizontalAlignment == HorizontalAlignment.LEFT:
                initX = self.leftMargin
            elif self.horizontalAlignment == HorizontalAlignment.CENTER:
                initX = mean( self.leftMargin, self.width - self.rightMargin )
            elif self.horizontalAlignment == HorizontalAlignment.RIGHT:
                initX = self.width - self.rightMargin
        

            if self.verticalAlignment == VerticalAlignment.TOP:
                initY = self.height - self.topMargin - self.rowHeights[0]
            elif self.verticalAlignment == VerticalAlignment.CENTER:
                initY = (
                    mean(self.height - self.topMargin, self.bottomMargin) # //this is the y-coordinate of the vertical center
                    + heightOfAllText/2 
                    - self.rowHeights[0]
                )
            elif self.verticalAlignment == VerticalAlignment.BOTTOM:
                initY = self.bottomMargin + heightOfAllText - self.rowHeights[0]
            
            insertionPoint = vector(initX, initY , initZ)

            for i in range(len(linesOfText)): # (var i = 0; i<size(linesOfText); i+=1):  
                lineOfText = linesOfText[i]
                thisTextRow = TextRow(
                    text = lineOfText,
                    fontName = self.fontNames[i % len(self.fontNames)],
                    characterHeight = self.rowHeights[i % len(self.rowHeights)]
                )  
                
                if self.horizontalAlignment == HorizontalAlignment.LEFT:
                    thisTextRow.translate(*insertionPoint)
                elif self.horizontalAlignment == HorizontalAlignment.CENTER:
                    thisTextRow.translate(*(insertionPoint - thisTextRow.width/2 * xHat))
                elif self.horizontalAlignment == HorizontalAlignment.RIGHT:
                    thisTextRow.translate(*(insertionPoint - thisTextRow._width * xHat))
                
                returnValue += [ x.brep for x in thisTextRow.bodies ] 

                insertionPoint += -yHat * self.rowSpacings[(i+1) % len(self.rowSpacings)] * self.rowHeights[(i+1) % len(self.rowHeights)] #//drop the insertion point down to be ready to start the next row.  
                
                # sheetBodiesInGalleySpace.append(thisTextRow.buildSheetBodiesInGalleySpace())
        
            if self.clipping :
                returnValue = [
                    body.brep
                    for body in
                    # fscad.Intersection(self.extentBox, fscad.BRepComponent(*returnValue)).bodies
                    #curiously, with the arguments to Intersection starting with extentBox, Intersection.bodies contains only a single empty body always,
                    # but reversing the order of the arguments produces the desired results -- this does not make sense; Intersection ought to be a totally commutative opearation.
                    # this might be a bug in fscad or in Fusion (in which case fscad ought to work around the fusion bug).
                    fscad.Intersection( fscad.BRepComponent(*returnValue), self.extentBox).bodies
                    

                    if body.brep.lumps.count > 0 # the intersection operation can return empty bodies. (the intersection of two disjoint bodies, for instance, is a body (or maybe a set of bodies) each of which is empty.
                ]
                # it might be worthwhile to detect whether the clipping operation 
                # actually resulted in anything being chopped off, and
                # record this fact in the Galley object for potential subsequent reference.
                # or to emit a warning if actual clipping occurs.
            
        return returnValue

class TextRow(fscad.BRepComponent):
    # todo: make all the properties read-only
    # a textrow is intended to be immutable.
    def __init__(self, 
        owningGalley : Optional[Galley] = None,
        text : str = "",
        fontName : str = "Arial", #"Tinos-Italic.ttf",
        characterHeight : float = 1 * inch,
        # basePoint = vector(0,0,0) * meter,
        name: str = None
    ):
        self._text = text
        self._fontName = fontName
        self._characterHeight = characterHeight 

        # propperties to be computed as a side effect of the construction of the bodies:
        # self.width 
        # self.opticalDepth 
        # self.opticalHeight

        # self.basePoint = basePoint 
        # basePoint is a position, in galleySpace (galleySpace is 3 dimensional,
        # although only the x and y dimensions are significant for the final
        # results) where the basepoint of this text row shall be located.
        # basePoint is, nominally, the lower-left corner of a row of text, but
        # it is defined in typographical/tex box sense rather than a strict
        # geometric/boundary sense, so that character shapes may stick down
        # below the basepoint or even extend to the left of it. 
        #
        # To be fully general, we might also want to allow a textRow to have an
        # arbitrary orientation, in addtion to having an arbitrary position.
        # However I have not yet implemented this behavior because the need for
        # it has not yet arisen.  At the moment, a textRow is always "upright"
        # within the galley.

        # update: we are departing from the behavior of the OnShape version of
        # this project by having TextRow not be a located row of text, but rather being an 
        # immutable row of text whose basepoint is implicitly at the origin.
        # Therefore, there will be no explicit basepoint property. (Or if there is, it better be read-only).

        #
        # The OnShape API did not provide a very clean way of specifying the
        # desired text height. Therefore, I had to rely on the fact that OnShape
        # API always produced text with a height of 1 unit, and then scale the
        # resulting entities in a separate operation (and I actually delayed the
        # scaling operation and rolled it into the final single transform that
        # transformed the "scale-free" entities directly into world space".
        # That's what all of the "scale-free" stuff was about in the
        # FeatureScript version of this code. Fortunately, the Fusion 360 API
        # does allow the desired text height to be specified as a first-class
        # parameter in the operation that generates the sketchText, so we don't
        # have to do the scaling as a separate operation.  (Conceivably, Fusion
        # might be applying the size-dependent shape changes that can be
        # specified in some of the fancier OpenType fonts, although I doubt that
        # it is.)

        tempOccurrence = fscad._create_component(
            parent_component = fscad.root(), 
            name="temp"
        )
        sketch = tempOccurrence.component.sketches.add(tempOccurrence.component.xYConstructionPlane, tempOccurrence)

        sketchTextInput = sketch.sketchTexts.createInput2(
            formattedText=self._text,
            height=self._characterHeight
        )

        class LayoutMode (Enum):
            multiline = enum.auto()
            alongPath = enum.auto()

        # layoutMode = LayoutMode.multiline
        layoutMode = LayoutMode.alongPath
        layoutDefiningPoints = [adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(5,0,0)]
        submitLayoutDefiningPointsInReverseOrder=False
        horizontalAlignment = adsk.core.HorizontalAlignments.LeftHorizontalAlignment
        characterSpacing = 0

        if layoutMode == LayoutMode.multiline:
            layoutDefiningPoints[1].y = 5
            sketchTextInput.setAsMultiLine(
                cornerPoint=layoutDefiningPoints[1 if submitLayoutDefiningPointsInReverseOrder else 0],
                diagonalPoint=layoutDefiningPoints[0 if submitLayoutDefiningPointsInReverseOrder else 1],
                horizontalAlignment=horizontalAlignment,
                verticalAlignment=adsk.core.VerticalAlignments.BottomVerticalAlignment,
                characterSpacing=characterSpacing
            )
        elif layoutMode == LayoutMode.alongPath:
            path = sketch.sketchCurves.sketchLines.addByTwoPoints(
                *(layoutDefiningPoints.reversed() if submitLayoutDefiningPointsInReverseOrder else layoutDefiningPoints)
            )
            sketchTextInput.setAsAlongPath(
                path=path,
                isAbovePath=True,
                horizontalAlignment=horizontalAlignment,
                characterSpacing=characterSpacing
            )


        ## OBSERVATIONS ON TEXT LAYOUT STRATEGIES---
         # "multiline" here doesn't imply or require that the text actually has
         # multiple lines, rather, "multiline" is one of the three layout
         # strategies (the others being AlongPath and FitOnPath). Of the three
         # layout strategie, only "multiline" allows text to have multiple lines
         # (I think). In our case, we are doing our own line layout (probably as
         # a vestige of the fact that we had to do our own line layout in
         # OnShape, whose text system was not as sophisticated as Fusion's, and
         # lacked built-in multiline capability.).
         #
         # as far as I can tell, the cornerPoint and diagonalPoint parameters
         # can be interchanged with no noticeable effect. As far as I can tell,
         # the only influence that these two parameters have on the position,
         # orientation, or size of the resulting text is that the position of
         # the lower-left-most of the two of those points is taken to be the
         # position of the resultant text, and if the two points are coincident,
         # or are horizontal or vertical to one another, fusion throws an error
         # ("RuntimeError: 2 : InternalValidationError : bSucceeded && text").  
         # fusion does draw sketch lines to form a rectangle, with the two
         # points as opposite corners, and the rectangle is constrained (not by
         # oifficial fusion constraints, but by some internal mechanism) so that
         # the corner of the rectangle that started out being the lower-left
         # most of the two points passed as arguments sets the position of the
         # text, and the lines are constrained to be a rectangle, and the
         # orientation of the text within the sketch is set to be along the side
         # of the rectangle that was originally the "bottom" side of the
         # rectangle. (I say originally, because the side that was originally
         # the bottom might cease to be the bottom as the rectangle is rotated,
         # but still the text will continue to stick to that original side. I
         # suspect that Fusion creates this rectangle as a convenience for the
         # user who wishes to control the placement of the text by means of
         # constraints. still -- it is quite confusing to have to think about
         # those two points, when really only one point matters. 
         #
         # for our purposes, we can set one of the two argument points (let's
         # choose diagonalPoint) to be anywhere above and to the right of the
         # other point, and then all that matters is the position of that other
         # point.
         #
         # Further discovery: I made all the above comments while having only
         # specified horizontalAlignment = LEft and verticalAlignment=Bottom.
         # But, upon trying different alignments, I realize that the rectangle
         # defined by the two points defines the horizontal and vertical
         # left/bottom, middle, and right/top positions. So, I have to retract
         # most of my above complaints/obeservations.  However, my observation
         # about the two arguments being completely interchangeable is still
         # correct, as far as I can tell.
         #
         # Fusion wraps text within the rectangle defined by cornerPoint and
         # diagonalPoint.  We do not want any wrapping.  The options for
         # preventing wrapping are to make the rectangle (nearly) infinitely
         # wide, or to use the AlongPath layout strategy.
         #
         # We want no wrapp
         #
         # Just as the cornerPoint and DiagonalPoint parameters of the
         # "multiline" layout strategy were interchangeable, it seems that when
         # doing the alongPath layout strategy with the path being a sketchLine
         # specified by its endpoints, the order of thje endpoints is completely
         # interchangeable.
         #
         # setting characterSpacing to large negative values can produce weird
         # results.
         #
         # The OnShape API provided no way to specify the horizontal alignment
         # of text, but it did allow you to read-out the natural width of a text
         # row, so we could then achieve the desired horizontal alignment by
         # moving the text according to the natural width and the desired
         # horizontal alignment. The Fusion API, by contrast, does provide a way
         # to specify the horizontal alignment when creating the text, and also
         # provides a way to read-out the natural width of the text (I think)
         # via the SketchText.BoundingBox property.  I am not sure whether to
         # continue to use the alignment strategy from the OnShape days, which
         # relies on reading out the natural width of the text, or whether to
         # rely on Fusion's own horizontalAlignment facilities.  I guess I am
         # inclined to continue using the OnShape-era technique.
         #
         # Left horizontal alignment seems to mean slightly different things in
         # the context of multiline layout as compared with alongPath layout:
         # with the multiline layout strategy, left alignment causes the
         # "optical" left edge of the character (by which I mean the left edge
         # of the bounding box of the reusltant ink) to be at the left alignment
         # point.  On the other hand, when using the alongPath layuout strategy,
         # left alignment seems to place the basepoint of the character's box
         # (in the tex sense) on the alignment point.  Acutally, that may not be
         # quite what is happening with alongPath layout, but there does end up
         # being a bit of a gap between the alignment point ant the optical left
         # edge of the character in the case of AlongPath layout.
         #
         # Curiously, the behavior of right horizontal alignment seems to be the
         # same in multiline and alongPath layout modes.


        sketchTextInput.fontName = self._fontName
        sketchTextInput.isHorizontalFlip = False
        sketchTextInput.isVerticalFlip = False
        sketchTextInput.textStyle = (
              0*adsk.fusion.TextStyles.TextStyleBold 
            + 0*adsk.fusion.TextStyles.TextStyleItalic 
            + 0*adsk.fusion.TextStyles.TextStyleUnderline
        )
        sketchText = sketch.sketchTexts.add(sketchTextInput)

        self._width = sketchText.boundingBox.maxPoint.x
        self._opticalDepth = min(0, -sketchText.boundingBox.minPoint.y)
        self._opticalHeight = max(0, sketchText.boundingBox.maxPoint.y)
                
        ## markers for debugging and experimention:
         # for radius in (0.4,0.38):
         #     sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint=layoutDefiningPoints[0] , radius=radius)
         # sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint=layoutDefiningPoints[1] , radius=0.4)
         # sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint=adsk.core.Point3D.create(0,0,0) , radius=0.06)
         #
         # highlight.highlight((sketchText.boundingBox.minPoint, sketchText.boundingBox.maxPoint))
         # FilledRectangle(
         #     sketchText.boundingBox.minPoint, 
         #     sketchText.boundingBox.maxPoint
         # ).buildSheetBodiesInGalleySpace().tz(-1).create_occurrence()
         # fscad.Sphere(radius=0.08,name="layoutPoint0_marker").translate(*castTo3dArray(layoutDefiningPoints[0])).create_occurrence()
         # fscad.Sphere(radius=0.04,name="layoutPoint1_marker").translate(*castTo3dArray(layoutDefiningPoints[1])).create_occurrence()


        super().__init__(
            *getAllSheetBodiesFromSketch(sketch),
            component = None, 
            name = name
        )
        tempOccurrence.deleteMe()

    @property
    def text(self) -> str:
        return self._text

    @property
    def fontName(self) -> str:
        return self._fontName

    @property
    def characterHeight(self) -> float:
        return self._characterHeight

    @property
    def width(self) -> float:
        return self._width

    @property
    def opticalDepth(self) -> float:
        return self._opticalDepth

    @property
    def opticalHeight(self) -> float:
        return self._opticalHeight

def getCannedBitHolders() -> Dict[str, BitHolder]:
    global _cannedBitHolders

    # construct _cannedBitHolders if it does not already exist
    if not _cannedBitHolders:

        cannedBitHolderSpecs = [
            {
                'name': "bondhus_hex_drivers_holder",
                'bitHolderParameters': {
                    'mountHolesPositionZStrategy': MountHolesPositionZStrategy.explicit,
                    'explicitMountHolesPositionZ': -10*millimeter,
                },
                'bitHolderSegmentParameters': {
                    'labelFontHeight'          : (4.75 * millimeter, 3.2*millimeter),
                    'lecternAngle'             : 70*degree,
                    'angleOfElevation'         : 70*degree,
                    'bitProtrusionStrategy'    : ProtrusionStrategy.explicitEmbedment,
                    'explicitBitEmbedment'     : 18 * millimeter
                },
                'commonBitParameters': {
                    'driveSize'       : 999.123456 * inch,
                    'length'          : 76.5 * millimeter,
                    'outerDiameter'   : (1/4) * inch * 1/cos(30*degree), 
                    # circumcscribed circle diameter of regular hexagon having inscribed circle diameter 1/4 inch.
                    'nominalUnit'     : 1*millimeter
                },
                'specificBitParameterses': [
                    # { 'nominalSize': 2    * millimeter                                                        },
                    # { 'nominalSize': 2.5  * millimeter                                                        },
                    # { 'nominalSize': 3    * millimeter                                                        },
                    # { 'nominalSize': 4    * millimeter                                                        },
                    # { 'nominalSize': 5    * millimeter                                                        },
                    # { 'nominalSize': 6    * millimeter                                                        },
                    # { 'nominalSize': 8    * millimeter,  'outerDiameter' : 8  * millimeter * 1/cos(30*degree) },
                    { 'nominalSize': 10   * millimeter,  'outerDiameter' : 10 * millimeter * 1/cos(30*degree) },
                    { 'nominalSize': 12   * millimeter,  'outerDiameter' : 12 * millimeter * 1/cos(30*degree) },
                ]
            },


            {
                'name': "3/8-inch drive, metric sockets holder",
                'bitHolderParameters': {

                },
                'bitHolderSegmentParameters': {
                    'labelFontHeight'          : 4.75 * millimeter,
                },
                'commonBitParameters': {
                    'driveSize':           3/8 * inch,
                    'length':              25.96 * millimeter,
                    'nominalUnit':        1*millimeter
                },
                'specificBitParameterses': [
                    { 'nominalSize': 10   * millimeter,   'outerDiameter': 17.18  * millimeter },
                    { 'nominalSize': 11   * millimeter,   'outerDiameter': 17.18  * millimeter },
                    { 'nominalSize': 12   * millimeter,   'outerDiameter': 17.8   * millimeter },
                    { 'nominalSize': 13   * millimeter,   'outerDiameter': 18.3   * millimeter },
                    { 'nominalSize': 14   * millimeter,   'outerDiameter': 19.71  * millimeter },
                    { 'nominalSize': 15   * millimeter,   'outerDiameter': 20.43  * millimeter },
                    { 'nominalSize': 17   * millimeter,   'outerDiameter': 23.36  * millimeter },
                    { 'nominalSize': 19   * millimeter,   'outerDiameter': 25.87  * millimeter }
                ]
            },
        ]

        _cannedBitHolders = {
            bitHolderSpec['name']: BitHolder(
                name=bitHolderSpec['name'],
                **bitHolderSpec['bitHolderParameters'],
                segments = (
                    BitHolderSegment(
                        **bitHolderSpec['bitHolderSegmentParameters'],
                        bit=Socket(**{**bitHolderSpec['commonBitParameters'], **specificBitParameters}),
                    )
                    for specificBitParameters in bitHolderSpec['specificBitParameterses']
                )
            )
            for bitHolderSpec in cannedBitHolderSpecs
        }



    return _cannedBitHolders

def makeBitHolderArray(*bitHolders : BitHolder, name=None) -> fscad.Component:
    workingBitHolders : List[BitHolder] = []
    insertionPoint :adsk.core.Point3D  = adsk.core.Point3D.create(0,0,0)
    insertionPoint
    for bitHolder in bitHolders:
        workingBitHolders.append(
            bitHolder.copy().translate(
                *adsk.core.Point3D.create(
                    bitHolder.mountHolePositions[0].x,
                    bitHolder.yMax,
                    bitHolder.mountHolePositions[0].z
                ).vectorTo(insertionPoint).asArray()
            )
        )
        
        
        insertionPoint.translateBy(adsk.core.Vector3D.create(0, 0, - 2 * inch))
    
    
    
    
    # return fscad.Union(*workingBitHolders, name=name) 
    
    
    # Whereas fscad.Group calls (or causes to be called) to _raw_bodies() method
    # of the specified objects both upon instantiation of the fscad.Group()
    # object and again upon running the Group object's create_occurence()
    # method, fscad.Union calls the _raw_bodies() method of the specified
    # components only once at time of instantiation.  Since I have not yet
    # implemented body caching for BitHolder, every call to a BitHolder's
    # _raw_bodies() method is expensive.  Therefore, for now, to reduce wait
    # time, I will use fscad.Union instead of fscad.Group().

    return fscad.Group(visible_children = workingBitHolders, name=name) 

#####################
