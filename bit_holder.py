from typing import Optional, Sequence, Union
from enum import Enum
import enum
import math
from .braids.fscad.src.fscad import fscad as fscad
from .highlight import *
import itertools

import scipy
# the above import of scipy requires the user to have taken action to ensure that scipy is available somewhere on the system path,
# for instance by doing "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install scipy
# I would like to automate the management of dependencies like this.  With a "normal" Python project, pipenv would be the logical way to do it,
# but for scripts that are to be loaded by fusion, it is unclear what the best way to manage dependencies is -- maybe some sort of vendoring?

from math import sin,cos,tan

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

# \b(?<containerName>(?<this>this)|(?:\w+))\[\]\.get_(?<propertyName>\w+)\(\)
# ==>
# (?{this}self:$+{containerName}).$+{propertyName}

# mean\(
# ==>
# np.mean(

class LabelSculptingStrategy(Enum):
    EMBOSS = enum.auto()
    ENGRAVE = enum.auto()

class Bit :
    """ a bit is essentially a cylinder along with a preferredLabelText property -- for our 
    purposes, these are the only aspects of a bit that we care about."""
    _defaultOuterDiameter = 17 * millimeter
    _defaultLength = 25 * millimeter
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
    def __init__(self):
        super().__init__()

    #TODO: fill in the details

class BitHolderSegment :
    def __init__(self):
        self.bit : Bit = Bit()
        
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
        self.bitHolder : BitHolder = BitHolder()
        self.bitHolder.segments = [self]
        # as a side effect of the above, 
        # self.bitHolder will be set to dummyBitHolder.

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
                    self.minimumAllowedExtentY,
                    # the minimum thickness to guarantee that the bore does not impinge on the mount hole or the clearance zone for the head of the mount screw.
                    self.bitHolder.mountHole.minimumAllowedClampingThickness
                    + self.bitHolder.mountHole.headClearanceHeight
                    + (
                        yHat
                        @ (
                            self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection)
                        )
                    )
            )
        
    @property
    def labelExtentX(self):
        if self.explicitLabelExtentX is not False:
            return self.explicitLabelExtentX
        else:
            return self.extentX - 0.4 * millimeter

    @labelExtentX.setter   
    #it would probably be better not to be so clever about the way to override the default-computer labelExtentX:
    # Rather than have a setter with side effects, we should have the user deal directly with explicitLabelExtentX 
    # and a flag that controls whether the override applies.     
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

    def build(self) -> fscad.Component:

        # var idOfInitialBodyCreationOperation = id + "mainBody";
        # // fCuboid(
        # //     context,
        # //     idOfInitialBodyCreationOperation,
        # //     {
        # //         corner1:vector(self.xMin,self.yMin,self.zMin),
        # //         corner2:vector(self.xMax,self.yMax,self.zMax)
        # //     }
        # // );
        
        # var polygonVertices = 
        #     [
        #         vector(self.yMin, zeroLength),
        #         vector(self.yMin, zeroLength) + vector(tan(self.lecternAngle) * self.zMax , self.zMax),
        #         vector(self.yMax,self.zMax),
        #         vector(self.yMax,self.zMin),
        #         vector(self.yMin,self.zMin),
        #     ];
        polygonVertices = [
                vector(self.xMin, self.yMin, zeroLength),
                vector(self.xMin, self.yMin + tan(self.lecternAngle) * self.zMax , self.zMax),
                vector(self.xMin, self.yMax, self.zMax),
                vector(self.xMin, self.yMax, self.zMin),
                vector(self.xMin, self.yMin, self.zMin),

                #vector(self.xMin, self.yMin, zeroLength), #do we need to repeat the initial point? no, and evidently, we mustn't repeat the initial point.  This might differ 
                # from the behavior of my OnShape function "createRightPolygonalPrism", which I think I would have made tolerant of a repeated final point.
            ]
        # print('self.minimumAllowedExtentY: ' + str(self.minimumAllowedExtentY))
        # print('self.bitHolder.mountHole.minimumAllowedClampingThickness: ' + str(self.bitHolder.mountHole.minimumAllowedClampingThickness))
        # print('self.bitHolder.mountHole.headClearanceHeight: ' + str(self.bitHolder.mountHole.headClearanceHeight))
        # print('self.boreDirection: ' + str(self.boreDirection))
        # print('self.boreDiameter: ' + str(self.boreDiameter))
        # print('self.extentY: ' + str(self.extentY))
        # print('yHat @ ( self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection)): ' + str(   
        #         yHat
        #         @ (
        #             self.boreBottomCenter + self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection)
        #         ) 
        #     )
        # )
        # print('self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection): ' + str(
        #         self.boreDiameter/2 * (rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection)
        #     )
        # )
        # print('rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection) ' + str(
        #         rotationMatrix3d(xHat, -90 * degree) @ self.boreDirection
        #     )
        # )
        # print('rotationMatrix3d(xHat, 90 * degree) ' + "\n" + str(
        #         rotationMatrix3d(xHat, 90 * degree)
        #     )
        # )
        polygonVertices.reverse()
        # the order of the vertices determines the direction of the face, which in turn determines the direction of the Extrude.
        # I would prefer to describe the extrude by giving a start point and an endpoint, but there is not at present 
        # a pre-existing function to do this.

        print(polygonVertices)
        highlight(
            itertools.starmap(
                adsk.core.Point3D.create,
                polygonVertices
            )
        )
        
        # createRightPolygonalPrism(
        #     context, 
        #     idOfInitialBodyCreationOperation, 
        #     {
        #         "plane": plane(vector(zeroLength,zeroLength,zeroLength), xHat, yHat),
        #         "vertices":
        #             polygonVertices,
        #         "height":self.extentX
        #     }
        # );
        
        # var mainBody = qBodyType(qCreatedBy(idOfInitialBodyCreationOperation, EntityType.BODY), BodyType.SOLID);
        # var returnValue = mainBody;

        polygon = fscad.Polygon(
            *itertools.starmap(
                adsk.core.Point3D.create,
                polygonVertices
            )
        )
        highlight(polygon)
        mainComponent = fscad.Extrude(polygon, height=self.extentX)
        

        # //we now have the mainBody, which we will proceed to modify below.
        # // As a side-effect of our modifications, we may end up with leftover bodies that were used for construction
        # // We want to be sure to delete any of these leftover bodies before we return from this build() function.
        # // we will collect throwaway entities that need to be deleted in throwAwayEntities:
        # // var throwAwayEntities = qNothing();
        # //Actually, I suspect that we might be able to accomplish this goal
        # // by doing an opDelete on a query that finds all bodies "created by" id, except mainBody.
        # // This will work assuming that qCreatedBy(id, EntityType.body), returns all bodies
        # // that were created by any operation whose id is descended from id, because all
        # // the operation ids that I construct in this build() function I construct
        # // using uniquid(context, id), and the uniqueid function returns an id that is descended from the input id.
        
        # //println("reportOnEntities(context, mainBody): " ~ reportOnEntities(context, mainBody, 0, 0));
        
        # // mapArray(
        # //     polygonVertices,
        # //     function(vertex)
        # //     {
        # //         var vertex3d = vector(zeroLength, vertex[0], vertex[1]);  
        # //         debug(context, vertex3d);
        # //     }
        # // );
        
        # var idOfBore = id + "bore";
        # var idOfBoreTool = id + "boretool";
        # // debug(context, qCreatedBy(idOfInitialBodyCreationOperation));
        # // debug(context, self.borePiercePoint);
        # // println("self.boreBottomCenter: " ~ toString(self.boreBottomCenter));		// self.boreBottomCenter
        # // println("self.boreTopCenter: " ~ toString(self.boreTopCenter));		// self.boreTopCenter
        # fCylinder(
        #     context,
        #     idOfBoreTool,
        #     {
        #         topCenter: self.boreTopCenter,
        #         bottomCenter: self.boreBottomCenter,
        #         radius: self.boreDiameter/2
        #     }
        # );
        # //debug(context, qCreatedBy(idOfBoreTool, EntityType.BODY));
        

        boreTool = fscad.Cylinder(height=1*meter,radius=self.boreDiameter/2)
        
        # to mimic the behavior of OnShape's fCylinder function, which lets you specify the cylinder's start
        # and end points, I must rotate so as to bring zHat into alignment with self.boreDirection,
        # and translate so as to move the origin to boreBottomCenter.
        
        t : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
        t.setToRotateTo(
            adsk.core.Vector3D.create(*zHat),
            adsk.core.Vector3D.create(*self.boreDirection)
        )
        t.translation = adsk.core.Vector3D.create(*self.boreBottomCenter)
        boreTool.transform(t)
        highlight(boreTool)
        # var idOfSplitFace = uniqueId(context,id);
        # opSplitFace(context,idOfSplitFace,
        #     {
        #         // faceTargets: qCreatedBy(idOfInitialBodyCreationOperation, EntityType.FACE),
        #         faceTargets: qOwnedByBody(mainBody, EntityType.FACE),
        #         bodyTools: qCreatedBy(idOfBoreTool, EntityType.BODY)
        #     }
        # );
        

        
        # opBoolean(context, idOfBore,
        #     {
        #         tools: qCreatedBy(idOfBoreTool, EntityType.BODY),
        #         targets: mainBody,
        #         operationType: BooleanOperationType.SUBTRACTION,
        #         targetsAndToolsNeedGrouping:true
        #     }
        # );
        # //debug(context, qCreatedBy(idOfSplitFace, EntityType.EDGE));
        # var edgesToFillet = qCreatedBy(idOfSplitFace, EntityType.EDGE);
        
        # var idOfFillet =  uniqueId(context,id);
        # try silent
        # {
        #     opFillet(context, idOfFillet,
        #         {
        #             entities:edgesToFillet,
        #             radius:self.mouthFilletRadius,
        #             tangentPropagation:false
        #         }
        #     );
        # }
        
        # var myGalley = new_galley();
        # myGalley[].fontName = self.labelFontName;
        # myGalley[].rowSpacing = 1.3; 
        # myGalley[].rowHeight = self.labelFontHeight;
        # myGalley[].text = self.labelText;
        # myGalley[].horizontalAlignment = horizontalAlignment.CENTER;
        # myGalley[].verticalAlignment = verticalAlignment.TOP;
        # myGalley[].clipping = true;
        # myGalley[].width = self.labelExtentX;
        # myGalley[].height = self.labelExtentZ;

        # myGalley[].anchor = galleyAnchor_e.CENTER;
        # myGalley[].worldPlane = 
        #     plane(
        #         /* origin: */ vector(
        #             mean([self.labelXMin, self.labelXMax]),
        #             self.labelYMin, 
        #             mean([self.labelZMin, self.labelZMax])
        #         ),
        #         /* normal: */ -yHat,
        #         /* x direction: */ xHat  
        #     );
        # var sheetBodiesInWorld = myGalley[].buildSheetBodiesInWorld(context, uniqueId(context,id));
        
        # var idOfLabelTool = uniqueId(context, id);
        # try
        # {
        #     opExtrude(
        #         context,
        #         idOfLabelTool,
        #         {
        #             entities:  qOwnedByBody(sheetBodiesInWorld, EntityType.FACE),
        #             direction: yHat,
        #             endBound: BoundingType.BLIND,
        #             endDepth: self.labelThickness,
        #             startBound: BoundingType.BLIND,
        #             startDepth: zeroLength
        #         }
        #     );
        # }
        
        # // sculpt (i.e. either emboss or engrave, according to this[].label.sculptingStrategy) the label tool onto the main body.
        # var idOfLabelSculpting = uniqueId(context,id);
        # try {opBoolean(context, idOfLabelSculpting,
        #     {
        #         tools: qCreatedBy(idOfLabelTool, EntityType.BODY),
        #         targets: mainBody,
        #         operationType:  (self.labelSculptingStrategy==labelSculptingStrategy.ENGRAVE ? BooleanOperationType.SUBTRACTION : BooleanOperationType.UNION),
        #         targetsAndToolsNeedGrouping:true, //regardless of whether the tool was kissing the main body, disjoint from the main body, or overlapping the main body, the feature failed unless targetsAndToolsNeedGrouping was true.  when kssing, a single Part was created.  When disjoint, two Part(s) were created.
        #         keepTools:false
        #     }
        # );}
        
        # if(self.doLabelRetentionLip){
        #     //the edges that we might want to sweep along are the set of edges e such that:
        #     // 1) e was created by the labelSculpting operation 
        #     // and 2) e bounds a face that existed before the label sculpting operation (i.e. a face that the labelSculpting operation modified but did not create.)
        #     // another way to state condition 2 is: e bounds a face that was not created by the label sculpting region.
        #     // another way to state condition 2 is: there exists a face not created by the label sculpting operation that owns e
            
        #     //var facesCreatedByTheLabelSculptingOperation = qCreatedBy(idOfLabelSculpting, EntityType.FACE);
        #     //println("facesCreatedByTheLabelSculptingOperation: ");print(reportOnEntities(context, facesCreatedByTheLabelSculptingOperation,0));
        #     //var sweepingEdgeCandidates = qCreatedBy(idOfLabelSculpting, EntityType.EDGE);
        #     var sweepingEdgeCandidates = qLoopEdges(qCreatedBy(idOfLabelSculpting, EntityType.FACE)); 
        #     //debug(context, sweepingEdgeCandidates);
        #     //debug(context, mainBody);
            
            
        #     // test case:
        #     // var sweepingEdges = qUnion(
        #     //     mapArray(
        #     //         connectedComponents(context, sweepingEdgeCandidates, AdjacencyType.VERTEX),
        #     //         function(x){return qUnion(array_slice(x,1));}
        #     //     )
        #     // );
        #     var sweepingEdges = qUnion(
        #         filter(
        #             evaluateQuery(context, sweepingEdgeCandidates)  ,
        #             function(sweepingEdgeCandidate){
        #                 var edgeTangentDirection = evEdgeTangentLine(context, {edge: sweepingEdgeCandidate, parameter: 0}).direction;
                        
        #                 // we return true iff. there is at least one element of get_directionsOfEdgesThatWeWillAddALabelRetentionLipTo() 
        #                 // to which sweepingEdgeCandidate is parallel.
        #                 for(var direction in self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo){
        #                     //evidently, the parallelVectors() function returns true in the case where the vectors parallel AND in
        #                     // the case where the vectors are anti-parallel.  That is an important fact that
        #                     // the documentation omits.
        #                     // fortunately, in our case, this is precisely the behavior that we want.
        #                     if(parallelVectors(edgeTangentDirection, direction)){
        #                         // if(dot(edgeTangentDirection, direction) < 0){
        #                         //     println(
        #                         //         "that's interesting, the parallelVectors() function regards two vectors as parallel "
        #                         //         ~ " even though the angle between them is " ~ 
        #                         //         (acos(dot(normalize(edgeTangentDirection), normalize(direction)))/degree) //angleBetween(,direction) 
        #                         //         ~ " degrees, "
        #                         //         ~ "which is not zero."
        #                         //     );
        #                         //}
                                
        #                         return true;   
        #                     }
        #                 }
        #                 return false;
        #             }
        #         )
        #     );
            
            
        #     var lipBodies = qNothing();
            
        #     //we want to iterate over all connected chains of edges that exist within the set of sweepingEdges.
        #     //for each connected chain, we will sweep a lip.
        #     //var chainCandidates = connectedComponents(context, sweepingEdges, AdjacencyType.VERTEX);
            
        #     //println("size(chainCandidates): " ~ size(chainCandidates));
            
            
        #     // for(var chainCandidate in chainCandidates){
        #     //     println("size(chainCandidate): " ~ size(chainCandidate));
        #     //     for(var chainCandidateElement in chainCandidate){
        #     //         debug(context, chainCandidateElement) ;  
        #     //     }
        #     // }
            
        #     var chains = mapArray(
        #         connectedComponents(context, sweepingEdges, AdjacencyType.VERTEX),
        #         function(x){return qUnion(x);}
        #     );
            
            
            
        #     //println("size(chains): " ~ size(chains));
        #     //debug(context, chains[1]);
        #     //for(var chain in chains){
        #     //    debug(context, chain);   
        #     //}
            

            
            
        #     var weAreOnTheFirstIteration = true;
        #     if(false){
        #         for (var sweepingEdge in evaluateQuery(context, sweepingEdgeCandidates)){
                    
        #             var hostFace = qSubtraction(
        #                 qAdjacent(sweepingEdge, AdjacencyType.EDGE, EntityType.FACE),
        #                 qCreatedBy(idOfLabelSculpting)
        #             );
                    
        #             if(weAreOnTheFirstIteration){println("hostFace: ");print(reportOnEntities(context, hostFace,0,0));}
                    
        #             // var yDirection = -yHat;
        #             // In our case, we have constructed things above so that we know that the normal
        #             // of the host facce is -yHat.  However, let's write this in a way that would work generally:
        #             var yDirection = evFaceNormalAtEdge(context,
        #                 {
        #                     edge: sweepingEdge,
        #                     face: hostFace,
        #                     parameter: 0
        #                 }
        #             );
                    
        #             var edgeTangentLine = evEdgeTangentLine(context, {
        #                 edge: sweepingEdge, 
        #                 parameter: 0,
        #                 // face is expected to be a face adjacent to edge.  The direction of the returned
        #                 // tangent line will be such that when walking in that direction with the face 
        #                 // normal being "up", the face will be on the left.
        #                 // the face that we want to use (which might now no longer exist) is the face of the
        #                 // ink sheet (the face such that gazing ant-parallel to the face's normal at the text, we will 
        #                 // see the text in the "correct" chirality (i.e. not a mirror image))
        #                 //because that face probably doesn't exist any more (it was a temporary construction thing to create the extruded text),
        #                 //we will instead provide the OTHER face that owns sweeping edge, namely, the face that the extruded text was cut into (or 
        #                 // embossed out of (the face whose normal is yDirection)
        #                 face: hostFace
        #             });
                    
        #             var zDirection =  -edgeTangentLine.direction;
                    
                    
        #             var labelRetentionLipCrossSectionSheetBody = createPolygonalSheetBody(context, uniqueId(context, id),
        #                 {
        #                     //we want a coordinate system whose y axis points "up" out of the pocket. 
        #                     // whose z axis is along (tangent or anti-tangent) to the edge, directed in such a way so 
        #                     // that the x axis points "off the edge of the cliff"
        #                     // and whose origin is on the edge
        #                     "coordSystem": 
        #                         coordSystem(
        #                             /* origin: */ 
        #                             //I am assuming that the origin of the line returned by evEdgeTangentLine is the tangent point.
        #                             //This is not guaranteed anywhere in the documentation, but ios probably a safe assumption.
        #                             edgeTangentLine.origin,
                                        
        #                             /* xAxis:  */  
        #                             cross(yDirection, zDirection), 
                                    
        #                             /* zAxis:  */  
        #                             zDirection
        #                         ),
        #                     "vertices": self.labelRetentionLipProfile
        #                 }                        
        #             );
        #             if(weAreOnTheFirstIteration){debug(context, labelRetentionLipCrossSectionSheetBody);}
        #             //if(weAreOnTheFirstIteration){debug(context, qOwnedByBody(labelRetentionLipCrossSectionSheetBody, EntityType.EDGE));}
        #             var faceToSweep = qOwnedByBody(labelRetentionLipCrossSectionSheetBody, EntityType.FACE);
        #             if(weAreOnTheFirstIteration){println("faceToSweep: ");print(reportOnEntities(context, faceToSweep,0,0));}
                    
        #             var idOfLipSweep = uniqueId(context, id);
                    
        #             opSweep(context, idOfLipSweep,
        #                 {
        #                     profiles: faceToSweep,
        #                     path: sweepingEdge,
        #                     keepProfileOrientation: false,
        #                     lockFaces: qNothing()
        #                 }
        #             );
                    
        #             var lipBody = qCreatedBy(idOfLipSweep, EntityType.BODY);
        #             lipBodies = qUnion([lipBodies, lipBody]);
        #             //if(weAreOnTheFirstIteration){debug(context, lipBody);}
        #             if(weAreOnTheFirstIteration){println("lipBody: ");print(reportOnEntities(context, lipBody,0,0));}
                    
                    
        #             if(weAreOnTheFirstIteration){
        #                 var idOfOperationToCreateDisposableCopyOfMainBody = uniqueId(context, id);
        #                 opPattern(context, idOfOperationToCreateDisposableCopyOfMainBody,
        #                     {
        #                         entities: mainBody,
        #                         transforms: [identityTransform()],
        #                         instanceNames: ["disposableCopy"],
        #                         copyPropertiesAndAttributes: true
        #                     }
        #                 );
                        
        #                 var disposableCopyOfMainBody = qCreatedBy(idOfOperationToCreateDisposableCopyOfMainBody, EntityType.BODY);
        #                 var idOfOperationJoiningLipBodyToTheDisposableCopyOfTheMainBody = uniqueId(context, id);
        #                 opBoolean(context,idOfOperationJoiningLipBodyToTheDisposableCopyOfTheMainBody,
        #                     {
        #                         operationType: BooleanOperationType.UNION,
        #                         tools: qUnion([ disposableCopyOfMainBody, lipBody ]),
        #                         //targets: qNothing(),
        #                         keepTools:false,
        #                         //targetsAndToolsNeedGrouping: false,
        #                         //matches: [],
        #                         //recomputeMatches: false
        #                     }
        #                 ); 
        #                 if(weAreOnTheFirstIteration){debug(context, disposableCopyOfMainBody);}
        #                 //if(weAreOnTheFirstIteration){debug(context, qOwnedByBody(disposableCopyOfMainBody, EntityType.EDGE));}
        #             }
                    
                    
                    
        #             weAreOnTheFirstIteration = false;
        #         }  
        #     }
            
            
        #     for (var chain in chains){
                
        #         var sampleEdge = qNthElement(chain, 0);
        #         var hostFace = qSubtraction(
        #             qAdjacent(sampleEdge, AdjacencyType.EDGE, EntityType.FACE),
        #             qCreatedBy(idOfLabelSculpting)
        #         );
                
        #         //if(weAreOnTheFirstIteration){println("hostFace: ");print(reportOnEntities(context, hostFace,0,0));}
                
        #         // var yDirection = -yHat;
        #         // In our case, we have constructed things above so that we know that the normal
        #         // of the host facce is -yHat.  However, let's write this in a way that would work generally:
        #         var yDirection = evFaceNormalAtEdge(context,
        #             {
        #                 edge: sampleEdge,
        #                 face: hostFace,
        #                 parameter: 0
        #             }
        #         );
                
        #         var edgeTangentLine = evEdgeTangentLine(context, {
        #             edge: sampleEdge, 
        #             parameter: 0,
        #             // face is expected to be a face adjacent to edge.  The direction of the returned
        #             // tangent line will be such that when walking in that direction with the face 
        #             // normal being "up", the face will be on the left.
        #             // the face that we want to use (which might now no longer exist) is the face of the
        #             // ink sheet (the face such that gazing ant-parallel to the face's normal at the text, we will 
        #             // see the text in the "correct" chirality (i.e. not a mirror image))
        #             //because that face probably doesn't exist any more (it was a temporary construction thing to create the extruded text),
        #             //we will instead provide the OTHER face that owns sweeping edge, namely, the face that the extruded text was cut into (or 
        #             // embossed out of (the face whose normal is yDirection)
        #             face: hostFace
        #         });
                
        #         var zDirection =  -edgeTangentLine.direction;
                
                
        #         var labelRetentionLipCrossSectionSheetBody = createPolygonalSheetBody(context, uniqueId(context, id),
        #             {
        #                 //we want a coordinate system whose y axis points "up" out of the pocket. 
        #                 // whose z axis is along (tangent or anti-tangent) to the edge, directed in such a way so 
        #                 // that the x axis points "off the edge of the cliff"
        #                 // and whose origin is on the edge
        #                 "coordSystem": 
        #                     coordSystem(
        #                         /* origin: */ 
        #                         //I am assuming that the origin of the line returned by evEdgeTangentLine is the tangent point.
        #                         //This is not guaranteed anywhere in the documentation, but ios probably a safe assumption.
        #                         edgeTangentLine.origin,
                                    
        #                         /* xAxis:  */  
        #                         cross(yDirection, zDirection), 
                                
        #                         /* zAxis:  */  
        #                         zDirection
        #                     ),
        #                 "vertices": self.labelRetentionLipProfile
        #             }                        
        #         );
        #         //if(weAreOnTheFirstIteration){debug(context, labelRetentionLipCrossSectionSheetBody);}
        #         //if(weAreOnTheFirstIteration){debug(context, qOwnedByBody(labelRetentionLipCrossSectionSheetBody, EntityType.EDGE));}
        #         var faceToSweep = qOwnedByBody(labelRetentionLipCrossSectionSheetBody, EntityType.FACE);
        #         //if(weAreOnTheFirstIteration){println("faceToSweep: ");print(reportOnEntities(context, faceToSweep,0,0));}
                
        #         var idOfLipSweep = uniqueId(context, id);
                
        #         try{
        #             opSweep(context, idOfLipSweep,
        #                 {
        #                     profiles: faceToSweep,
        #                     path: chain,
        #                     keepProfileOrientation: false,
        #                     lockFaces: qNothing()
        #                 }
        #             );
        #         } catch (error){
        #             println("An exception occured during sweep: " ~ toString(error));
        #             println(toString(getFeatureStatus(context, idOfLipSweep)));
        #         }
                
                
                
        #         var lipBody = qCreatedBy(idOfLipSweep, EntityType.BODY);
        #         if(queryReturnsSomething(context, lipBody)){
                    
        #             lipBodies = qUnion([lipBodies, lipBody]);
        #             //debug(context, qOwnedByBody(lipBody,EntityType.EDGE));
        #             //if(weAreOnTheFirstIteration){println("lipBody: ");print(reportOnEntities(context, lipBody,0,0));}
                    
                    
        #             if(false){
        #                 var idOfOperationToCreateDisposableCopyOfMainBody = uniqueId(context, id);
        #                 opPattern(context, idOfOperationToCreateDisposableCopyOfMainBody,
        #                     {
        #                         entities: mainBody,
        #                         transforms: [identityTransform()],
        #                         instanceNames: ["disposableCopy"],
        #                         copyPropertiesAndAttributes: true
        #                     }
        #                 );
        #                 var disposableCopyOfMainBody = qCreatedBy(idOfOperationToCreateDisposableCopyOfMainBody, EntityType.BODY);
                        
        #                 var idOfOperationToCreateDisposableCopyOfLipBody = uniqueId(context, id);
        #                 opPattern(context, idOfOperationToCreateDisposableCopyOfLipBody,
        #                     {
        #                         entities: lipBody,
        #                         transforms: [identityTransform()],
        #                         instanceNames: ["disposableCopy"],
        #                         copyPropertiesAndAttributes: true
        #                     }
        #                 );
        #                 var disposableCopyOfLipBody = qCreatedBy(idOfOperationToCreateDisposableCopyOfLipBody, EntityType.BODY);
                        
                        
                        
        #                 var idOfOperationJoiningTheDisposableCopyOfLipBodyToTheDisposableCopyOfMainBody = uniqueId(context, id);
        #                 opBoolean(context,idOfOperationJoiningTheDisposableCopyOfLipBodyToTheDisposableCopyOfMainBody,
        #                     {
        #                         operationType: BooleanOperationType.UNION,
        #                         tools: qUnion([ disposableCopyOfMainBody, disposableCopyOfLipBody ]),
        #                         //targets: qNothing(),
        #                         keepTools:false,
        #                         //targetsAndToolsNeedGrouping: false,
        #                         //matches: [],
        #                         //recomputeMatches: false
        #                     }
        #                 ); 
        #                 if(weAreOnTheFirstIteration){debug(context, disposableCopyOfMainBody);}
        #                 //if(weAreOnTheFirstIteration){debug(context, qOwnedByBody(disposableCopyOfMainBody, EntityType.EDGE));}
        #             }
        #         }
                
                
                
        #         weAreOnTheFirstIteration = false;
        #     }
            
            
        #     //println("lipBodies: ");print(reportOnEntities(context, lipBodies,0,0));
        #     var idOfOperationJoiningLipsToTheMainBody = uniqueId(context, id);
            
            
            
        #     try{
        #         opBoolean(context,idOfOperationJoiningLipsToTheMainBody,
        #             {
        #                 operationType: BooleanOperationType.UNION,
        #                 tools: qUnion([mainBody, lipBodies]),
        #                 //targets: qNothing(),
        #                 //keepTools:false,
        #                 //targetsAndToolsNeedGrouping: false,
        #                 //matches: [],
        #                 //recomputeMatches: false
        #             }
        #         );
        #     }
                
        #     //just in case the lipBodies are not in contact with the main body:
        #     returnValue = qUnion([returnValue, qCreatedBy(idOfOperationJoiningLipsToTheMainBody, EntityType.BODY)]);
        #     //this probably isn't necessary    
                
            
        # }
        
        # var leftoverBodiesToBeDeleted = qSubtraction(
        #     qCreatedBy(id, EntityType.BODY),
        #     returnValue
        # );
        
        # //println("leftoverBodiesToBeDeleted: ");print(reportOnEntities(context, leftoverBodiesToBeDeleted,0,0));
        
        # try {opDeleteBodies(context, uniqueId(context, id), {entities: leftoverBodiesToBeDeleted}); }
        
        # // return qBodyType(qCreatedBy(idOfInitialBodyCreationOperation, EntityType.BODY), BodyType.SOLID);
        # //return mainBody;
        # //println("returnValue: " ~ reportOnEntities(context, returnValue,0,0));
        # return returnValue;


        return mainComponent
            

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
        self._segments : list[BitHolderSegment] = []
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

    @property
    def segments(self):
        return self._segments
    
    @segments.setter
    def segments(self, newSegments : 'list[BitHolderSegment]'):
        self._segments = newSegments
        for segment in self._segments:
            segment.bitHolder = self
    

class MountHole :
    """ a MountHole to be contained within a BitHolder.   """ 

    def __init__(self):
        self.shankClearanceDiameter = 3 * millimeter
        self.headClearanceDiameter = 8 * millimeter
        self.headClearanceHeight = 2.7 * millimeter
        self.minimumAllowedClampingThickness = 1/4 * inch
        self.clampingDiameter = 5/8 * inch
