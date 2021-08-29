from typing import Optional, Sequence, Union
from enum import Enum
import enum
import math

import scipy
# the above import of scipy requires the user to have taken action to ensure that scipy is available somewhere on the system path,
# for instance by doing "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install scipy
# I would like to automate the management of dependencies like this.  With a "normal" Python project, pipenv would be the logical way to do it,
# but for scripts that are to be loaded by fusion, it is unclear what the best way to manage dependencies is -- maybe some sort of vendoring?


import numpy as np
# I am relying on the installation of scipy to also install numpy.

from numpy.typing import ArrayLike


import unyt
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt


from .bit_holder_utility import *


# regex substitution rules that were useful when converting the original featurescript code to python: 
# \bthis\[\]\.get_(\w+)\(\)
# ==>
# self.$1

# \bthis\[\]\.get_(\w+) = 
# ==>
# @property\n    def $1(self)

# \[\]\.get_(\w+)\(\)
# ==>
# .$1

# mean\(
# ==>
# np.mean(

class LabelSculptingStrategy(Enum):
    EMBOSS = enum.auto()
    ENGRAVE = enum.auto()

class Bit :
    """ a bit is essentially a cylinder along with a preferredLabelText property -- for our 
    purposes, these are the only aspects of a bit that we care about."""
    _defaultOuterDiameter = 17
    _defaultLength = 25
    _defaultPreferredLabelText = "DEFAULT"

    def __init__(self):
        self.outerDiameter : float = self._defaultOuterDiameter
        self.length        : float = self._defaultLength
        
        self.preferredLabelText : str = self._defaultPreferredLabelText

class Socket (Bit):
    """ Socket is a specialized type of (i.e. inherits from) Bit. the only
    thing that socket does differently is that it overrides the
    preferredLabelText property, and defines a couple of other properties to
    help specify preferredLabelText.
    """
    pass

class BitHolderSegment :
    def __init__(self):
        self.bit : Bit = Bit()
        self.bitHolder : Optional[BitHolder] = None
        self.angleOfElevation = 45 * degree
        self.lecternAngle = 45 * degree
        self.lecternMarginBelowBore = 3 * millimeter
        self.lecternMarginAboveBore = 3 * millimeter
        self.boreDiameterAllowance = 0.8 * millimeter
        self.mouthFilletRadius = 2*millimeter
    
        #this[].bitProtrusionY = 10 * millimeter;
        self.bitProtrusion = 10.6 * millimeter
        self.keepInkSheets = False #not yet implemented //a flag to control whether we keep the label's ink sheet bodies after we are finished with them.  This can be useful for visualizing text.
        self.labelExtentZ= 12 * millimeter
        self.labelThickness= 0.9 * millimeter #this is the thickness of the text (regardless of whether the text is engraved or embossed).
        self.labelZMax = - 1 * millimeter
        self.labelFontHeight = 4.75 * millimeter
        self.labelFontName = "NotoSans-Bold.ttf"
        self.labelSculptingStrategy = LabelSculptingStrategy.ENGRAVE # labelSculptingStrategy.EMBOSS;
        self.minimumAllowedExtentX = 12 * millimeter # used to enforce minimum interval between bits for ease of grabbing very small bits with fingers.
        self.minimumAllowedExtentY = 0 * millimeter  
        self.minimumAllowedLabelToZMinOffset = 0 * millimeter  
        self.minimumAllowedBoreToZMinOffset = 2 * millimeter 
        self.explicitLabelExtentX  = False
        self.doLabelRetentionLip = False 
        # This only makes sense in the case where we are using the
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
    
        self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo = [xHat]
        # we will not add a lip to all edges.  Rather, we will add a lip only to
        # edges that are parallel (possibly within some tolerance) (or
        # anti-parallel) to any of the specified directions.  (this is geared toward
        # the cases where edges are straight lines.)
    
    
        # //test case:
        # // this[].labelRetentionLipProfile = [
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

    @property
    def zMax(self):
        #   return
        #         max(
        #             10 * millimeter,
        #             # self.boreDiameter/cos(self.angleOfElevation) + this[].mouthFilletRadius + 1.1 * millimeter
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
                    self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, 90 * degree) * self.boreDirection)
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
                [
                    self.minimumAllowedExtentY,
                    # the minimum thickness to guarantee that the bore does not impinge on the mount hole or the clearance zone for the head of the mount screw.
                    self.bitHolder.mountHole.minimumAllowedClampingThickness
                    + self.bitHolder.mountHole.headClearanceHeight
                    + (
                        yHat
                        @ (
                            self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) * self.boreDirection)
                        )
                    )
                ]
            )
        
    @property
    def labelExtentX(self):
        if self.explicitLabelExtentX is not False:
            return self.explicitLabelExtentX
        else:
            return self.extentX - 0.4 * millimeter

    @labelExtentX.setter        
    def labelExtentX(self, x): 
        self.explicitLabelExtentX = x   

 
    @property
    def labelText(self):
        return self.bit.preferredLabelText # "\u0298" is a unicode character that, at least in the Tinos font, consists of a circle, like an 'O', and a central isolated dot.  This character does not extrude correctly (the middle dot is missng)

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
        return rotationMatrix3d(xHat, -self.angleOfElevation) * -yHat  #shooting out of the bore

    @property
    def boreDiameter(self):
        return self.bit.outerDiameter + self.boreDiameterAllowance
        
    @property
    def boreTopCenter(self):
        # //return 
        #     // vector(0, -1, tan(self.angleOfElevation))*self.bitProtrusionY
        #     // + self.boreDiameter/2 * (rotationMatrix3d(xHat,-90*degree)*self.boreDirection);
        return self.boreBottomCenter + 1 * meter * self.boreDirection

    @property
    def lecternNormal(self):
        return rotationMatrix3d(xHat, -self.lecternAngle) * -yHat
        
    @property
    def boreBottomCenter(self):
        # return self.boreTopCenter - self.boreDirection * self.bit.length;
        return self.borePiercePoint - self.boreDepth * self.boreDirection

    @property
    def bottomBoreCorner(self):
        return (
            self.origin - (rotationMatrix3d(xHat, 90*degree) * self.lecternNormal)
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
            (rotationMatrix3d(xHat, 90*degree) * self.lecternNormal)
            * (
                self.lecternMarginBelowBore
                + (1/2) * 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
            )
        )

    @property
    def topBoreCorner(self):
        return (
            self.origin - 
            (rotationMatrix3d(xHat, 90*degree) * self.lecternNormal)
            * (
                self.lecternMarginBelowBore
                + 1/sin(90*degree - self.angleOfElevation + self.lecternAngle) * self.boreDiameter
            )
        )

    @property
    def lecternTopPoint(self):
        return (
            self.origin - 
            (rotationMatrix3d(xHat, 90*degree) * self.lecternNormal)
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
                    rotationMatrix3d(xHat, 90*degree) * self.lecternNormal,
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
    # //                     rotationMatrix3d(xHat, 90*degree) * self.lecternNormal,
    # //                     -self.boreDirection
    # //                 )
    # //             );
    # //     };
        

    @property
    def bottomSaddlePointOfMouthFillet(self): #//see neil-4936          
        return self.bottomPointOfMouthFilletSweepPath + self.mouthFilletRadius * zHat

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

class BitHolder :
    """ a BitHolder is a collection of BitHolderSegment objects along with some
    parameters that specify how the bitHolderSegments are to be welded together 
    to make a single BitHolder.     """

    def __init__(self):
        self.segments : list[BitHolderSegment] = []
        self.mountHole : MountHole = MountHole()
        
        #these clearance diameters are appropriate for a UTS 8-32 pan-head screw.
        self.mountHole.shankClearanceDiameter            = 4.4958 * millimeter
        self.mountHole.headClearanceDiameter             = 8.6 * millimeter
        self.mountHole.minimumAllowedClampingThickness   = 3 * millimeter
        self.mountHole.clampingDiameter                  = 21 * millimeter
        self.mountHole.headClearanceHeight               = 2.7 * millimeter
        
        self.minimumAllowedExtentY = 12 * millimeter
    
        self.mountHolesGridSpacing = 1 * inch
        # the mountHolesInterval will be constrained to be an integer multiple of this length.
        self.mountHolesPositionZStrategy : MountHolesPositionZStrategy = MountHolesPositionZStrategy.grazeBottomOfSaddleBoreLip
        self.explicitMountHolesPositionZ  = zeroLength

    @property        
    def xMinMountHolePositionX(self):
        return 0.5 * self.mountHolesGridSpacing - 1.5 * millimeter; 
    
    @property
    def mountHolePositions(self):
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
                ) + self.mountHole.headClearanceDiameter/2
        
        elif self.mountHolesPositionZStrategy == MountHolesPositionZStrategy.middle :
            # strategy 3: z midpoint
            mountHolesPositionZ = mean(self.zMin, self.zMax)
        else:
            mountHolesPositionZ = zeroLength
        
        # compute the x coordinates of the mount hole positions
        if self.extentX < self.mountHolesGridSpacing:
            return []
        

        mountHolesInterval =  floor(
                self.extentX - self.xMinMountHolePositionX - self.mountHole.clampingDiameter/2 , 
                self.mountHolesGridSpacing
            )            
        mountHolePositions[0] = (
                #self.extentX/2 - mountHolesInterval/2,
                self.xMinMountHolePositionX,
                zeroLength,
                mountHolesPositionZ
            )

        mountHolePositions[1] = mountHolePositions[0] + mountHolesInterval * xHat            
        return  mountHolePositions 

    @property
    def extentX(self):
        return sum(
            map(
                lambda segment: segment.extentX,
                self.segments
            )
        )    
    
    @property
    def xMin(self):
        return zeroLength

    @property    
    def xMax(self):
        return self.xMin + self.extentX
    
    # caution: this modifies the segments in self.segments.
    def makeExtentYOfAllSegmentsTheSame(self) -> None :
        commonMinimumAllowedExtentY = max(
            *map(
                lambda segment: segment.extentY,
                self.segments
            ),
            self.minimumAllowedExtentY 
        )
  
        for segment in self.segments:
            segment.minimumAllowedExtentY = commonMinimumAllowedExtentY
    
    @property
    def zMax(self):
        return max(
            *map(
                lambda segment: segment.zMax,
                self.segments
            )
        )

    @property
    def zMin(self):
        return min(
            *map(
                lambda segment: segment.zMin,
                self.segments
            )
        )
    
    @property
    def extentZ(self):
        return self.zMax - self.zMin
    
    @property
    def yMin(self):
        return min(
            *map(
                lambda segment: segment.yMin,
                self.segments
            )
        )

    @property
    def yMax(self):
        return max(
            *map(
                lambda segment: segment.yMax,
                self.segments
            )
        )
    
    @property
    def extentY(self):
        return self.yMax - self.yMin

class MountHole :
    """ a MountHole to be contained within a BitHolder.   """ 

    def __init__(self):
        self.shankClearanceDiameter = 3 * millimeter
        self.headClearanceDiameter = 8 * millimeter
        self.headClearanceHeight = 2.7 * millimeter
        self.minimumAllowedClampingThickness = 1/4 * inch
        self.clampingDiameter = 5/8 * inch
