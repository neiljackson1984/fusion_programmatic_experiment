from typing import Optional, Sequence, Tuple, Union
from enum import Enum
import enum
import math
from .braids.fscad.src.fscad import fscad as fscad
from .highlight import *
import itertools
import re

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


    def __init__(self,
        outerDiameter        : float = 17 * millimeter,
        length               : float = 25 * millimeter,
        preferredLabelText   : str   = "DEFAULT"
    ):
        self.outerDiameter      : float = outerDiameter
        self.length             : float = length
        self.preferredLabelText : str   = preferredLabelText

class Socket (Bit):
    """ Socket is a specialized type of (i.e. inherits from) Bit. the only
    thing that socket does differently is that it overrides the
    preferredLabelText property, and defines a couple of other properties to
    help specify preferredLabelText.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #TODO: fill in the details

class BitHolderSegment (fscad.BRepComponent)  :
    def __init__(self, 
        bit                                                : Optional[Bit]           = None,
        bitHolder                                          : Optional['BitHolder']   = None,
        angleOfElevation                                   : float                   = 45   * degree,
        lecternAngle                                       : float                   = 45   * degree,
        lecternMarginBelowBore                             : float                   = 3    * millimeter,
        lecternMarginAboveBore                             : float                   = 3    * millimeter,
        boreDiameterAllowance                              : float                   = 0.8  * millimeter,
        mouthFilletRadius                                  : float                   = 2    * millimeter,
        bitProtrusion                                      : float                   = 10.6 * millimeter,
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
        directionsOfEdgesThatWeWillAddALabelRetentionLipTo : Sequence                = [xHat],
    
        name                                               : str = None 
    
    
    ):
        self.bit                                                 : Bit         = (bit if bit is not None else Bit())
        self.bitHolder                                           : BitHolder   = (bitHolder if bitHolder is not None else BitHolder(segments = [self]))
        self.angleOfElevation                                    : float       = angleOfElevation
        self.lecternAngle                                        : float       = lecternAngle
        self.lecternMarginBelowBore                              : float       = lecternMarginBelowBore
        self.lecternMarginAboveBore                              : float       = lecternMarginAboveBore
        self.boreDiameterAllowance                               : float       = boreDiameterAllowance
        self.mouthFilletRadius                                   : float       = mouthFilletRadius
        self.bitProtrusion                                       : float       = bitProtrusion
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
        self.directionsOfEdgesThatWeWillAddALabelRetentionLipTo  : Sequence    = directionsOfEdgesThatWeWillAddALabelRetentionLipTo
        
           
        
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

        super().__init__(
            *self._build(),
            component = None, 
            name = name
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

    def _build(self) -> Sequence[adsk.fusion.BRepBody]:
        returnValue : list[adsk.fusion.BRepBody] = []
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

        # print(polygonVertices)
        # highlight(
        #     itertools.starmap(
        #         adsk.core.Point3D.create,
        #         polygonVertices
        #     )
        # )
        
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
        # highlight(polygon)
        mainPrivateComponent : fscad.Component
        mainPrivateComponent : fscad.Component = fscad.Extrude(polygon, height=self.extentX)
        

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
        # highlight(boreTool)
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
        
        boxOccurrence = mainPrivateComponent.create_occurrence()
        boxBody = boxOccurrence.bRepBodies.item(0)
        boreToolOccurrence = boreTool.create_occurrence()
        boreToolBody = boreToolOccurrence.bRepBodies.item(0)

        def captureEntityTokens(occurrence : adsk.fusion.Occurrence):
            return {
                'occurrence': occurrence.entityToken,
                'component': occurrence.component.entityToken,
                'bodies' : [
                    {
                        'body'  : body.entityToken,
                        'faces' : [face.entityToken for face in body.faces],
                        'edges' : [edge.entityToken for edge in body.edges]
                    }
                    for body in occurrence.bRepBodies
                ]
            }

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
        # highlight(edgesOfInterest)
        # print('len(edgesOfInterest): ' + str(len(edgesOfInterest)))


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
        
        filletFeatureInput = boxOccurrence.component.features.filletFeatures.createInput()

        filletFeatureInput.addConstantRadiusEdgeSet(
            edges= fscad._collection_of(edgesOfInterest),
            radius= adsk.core.ValueInput.createByReal(self.mouthFilletRadius),
            isTangentChain=False
        )

        filletFeature = boxOccurrence.component.features.filletFeatures.add(filletFeatureInput)
        
        mainPrivateComponent = fscad.BRepComponent(*boxOccurrence.bRepBodies)

        # returnValue += [
        #     fscad.brep().copy(x)
        #     for x in boxOccurrence.bRepBodies
        # ]
        # it is probably somewhat inefficient to copy the bodies here, because they will just be fed into the constructor for BRepComponent, which will copy them again.
        # Ideally, I would leave the temporary boxOccurence in place until I had called the BRepComponent constructor, and then delete the temporary occurence.

        boxOccurrence.deleteMe()
        # returnValue += [
        #     x.brep 
        #     for x in TextRow(
        #         fontName="Times New Roman",
        #         text="Abc"
        #     ).bodies
        # ]




        myGalley = Galley(
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



        # myGalley.anchor = GalleyAnchor_e.CENTER

        # # myGalley.worldPlane = 
        # #     plane(
        # #         /* origin: */ vector(
        # #             mean([self.labelXMin, self.labelXMax]),
        # #             self.labelYMin, 
        # #             mean([self.labelZMin, self.labelZMax])
        # #         ),
        # #         /* normal: */ -yHat,
        # #         /* x direction: */ xHat  
        # #     );

        t = adsk.core.Matrix3D.create()
        xAxis  = castToVector3d(xHat)
        zAxis  = castToVector3d(-yHat)
        yAxis = zAxis.copy().crossProduct(xAxis)
        t.setWithCoordinateSystem(
            origin = adsk.core.Point3D.create(self.labelXMin, self.labelYMin, self.labelZMin),
            xAxis  = xAxis,
            yAxis  = yAxis,
            zAxis  = zAxis
        )
        myGalley.transform(t)

        
        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in myGalley.bodies
        # ]


        # sheetBodiesInWorld = myGalley.buildSheetBodiesInWorld(context, uniqueId(context,id))

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
        
        #extrude myGalley to form labelSculptingTool
        # labelSculptingTool = fscad.Extrude(myGalley, self.labelThickness)
        

        # in the case where len(myGalley.bodies) == 0 (which happens, for instance, when 
        # labelText is an empty string or a string containing only whitepsace),
        # the above fscad.Extrude operation throws an exception saying "can't extrude non-planer geometry with Extrude".
        # I would propose modifying fscad.Extrude to be tolerant of the case of extruding an empty component.
        # True, the empty component is not planar, but it can certainly be extruded - the result is trivial -- namely no bodies.
        # Come on people; zero exists.

        labelSculptingTool = (
            fscad.Extrude(myGalley, -self.labelThickness)
            # I would like to be able to specify or hint at an extrude direction, or specify
            # start and end points, rather than relying on the vagueries of the face direction
            # (which at least are consistent and predictable here -- actually they are not consistent
            # the filled rectangle seems to point in a different direction from the text.).
            # TODO, within Galley._build, ensure that the rect points up.  I suspect that, at the moment it points down.
            # (or maybe the problem is with getAllSheetBodiesFromSketch returning faces whose normal is 
            # pointing counter to the sketch's normal -- yes I suspect that is the problem.
            if len(myGalley.bodies) > 0
            else fscad.BRepComponent() # this is simply an empty component.
        )

        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in labelSculptingTool.bodies
        # ]

        # returnValue += [
        #     fscad.brep().copy(x.brep)
        #     for x in myGalley.bodies
        # ]

        # // sculpt (i.e. either emboss or engrave, according to self.labelSculptingStrategy) the label tool onto the main body.
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

        if self.labelSculptingStrategy == LabelSculptingStrategy.EMBOSS:
            mainPrivateComponent = fscad.Union(mainPrivateComponent, labelSculptingTool)
        elif self.labelSculptingStrategy == LabelSculptingStrategy.ENGRAVE:
            mainPrivateComponent = fscad.Difference(mainPrivateComponent, labelSculptingTool)
        
        returnValue += [
            fscad.brep().copy(x.brep)
            for x in mainPrivateComponent.bodies
        ]
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
                        
        #                 // we return true iff. there is at least one element of directionsOfEdgesThatWeWillAddALabelRetentionLipTo
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


        return returnValue
            
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

class BitHolder  (fscad.BRepComponent) :
    """ a BitHolder is a collection of BitHolderSegment objects along with some
    parameters that specify how the bitHolderSegments are to be welded together 
    to make a single BitHolder.     """

    def __init__(self,
            segments                                           : Sequence[BitHolderSegment],
            name                                               : str = None 
        ):
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

        # super().__init__(
        #     *self._build(),
        #     component = None, 
        #     name = name
        # )


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


def castToNDArray(x: Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D], n: Optional[int] = None) -> NDArray:
    #TODO: handle various ranks of NDArray rather than blindly assuming that we have been given a rank-1 array.
    if isinstance(x, np.ndarray):
        returnValue = x
    elif isinstance(x, adsk.core.Point3D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Vector3D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Point2D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Vector2D):
        returnValue =  np.array(x.asArray())
    else:
        returnValue =  np.array(x)

    if n is not None:
        #pad with zeros as needed to make sure we have at least n elements:
        returnValue = np.append(
            returnValue, 
            (0,)*(n-len(returnValue))
        )
        #take the first n elements, to ensure that we end up with exactly n elements:
        returnValue = returnValue[0:n]
        # this cannot possibly be the most efficient way to do this, 
        # but it has the advantage of being a fairly short line of code.
    return returnValue

def castTo3dArray(x: Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D]) -> NDArray: 
    #need to figure out how to use the shape-specificatin facility that I think is part of the NDArray type alias.
    a=castToNDArray(x, 3)
    # I am not sure whether what we should do with Point2D and Vector2D: should we treat them like Point3D and Vector3D that 
    # happen to lie in the xy plane, or should we return the point in projective 3d space that they represent?
    # for now, I am treating them like Point3D and Vector3D that happen to lie in the xy plane.
    #TODO: handle various sizes of NDArray rather than blindly assuming that we have been given a 3-array
    return a

def castTo4dArray(x: Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D]) -> NDArray: 
    #need to figure out how to use the shape-specificatin facility that I think is part of the NDArray type alias.
    a=castToNDArray(x,4)
    if isinstance(x, (adsk.core.Point3D, adsk.core.Point2D)):
        a[3] = 1


    return a

def castToPoint3d(x: Union[adsk.core.Point3D, ndarray, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D]) -> adsk.core.Point3D:
    if isinstance(x, adsk.core.Point3D):
        return x
    else:
        return adsk.core.Point3D.create(*castTo3dArray(x))


def castToVector3d(x: Union[adsk.core.Point3D, ndarray, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D]) -> adsk.core.Vector3D:
    if isinstance(x, adsk.core.Vector3D):
        return x
    else:
        return adsk.core.Vector3D.create(*castTo3dArray(x))

# we can think of adsk.core.Vector3D and adsk.core.Point3D as being special
# cases of a 4-element sequence of reals.  Vector3D has the last element being 0
# and Point3D has the last element being 1.  This produces the correct behavior
# when we transform a Vector3D or a Point3D by multiplying by a 4x4 matrix on
# the left.  Therefore, it might make sense to have a castTo4DArray that treats 
# Vector3D and Point3D objects correctly.  

# an alternate constructor for fscad.Rect:
def rectByCorners(corner1 = vector(0,0) * meter, corner2 = vector(1,1) * meter, *args, **kwargs) -> fscad.Rect:
    corner1 = castTo3dArray(corner1)
    corner2 = castTo3dArray(corner2)
    # print('corner1: ' + str(corner1))
    # print('corner2: ' + str(corner2))
    # set the 'x' and 'y' entries to kwargs (overriding any 'x' and 'y' that may have been passed)

    extent = abs(corner2 - corner1)
    minimumCorner = tuple(map(min, corner1, corner2))
    # minimumCorner = map(float, minimumCorner)
    # print('minimumCorner: ' + str(minimumCorner))   
    # print('type(minimumCorner[0]): ' + str(type(minimumCorner[0])))   
    # v = adsk.core.Vector3D.create(minimumCorner[0], minimumCorner[1], minimumCorner[2])
    # v = adsk.core.Vector3D.create(*minimumCorner)

    return fscad.Rect(
        x=extent[0],
        y=extent[1],
        *args,
        **kwargs,
    ).translate(*map(float,minimumCorner))
    # it is very hacky to have to cast to float above, but that
    # is what we have to do to work around Python's lack of
    # automatic type coercion.


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


        # highlight(fscad.Rect(self.width, self.height).edges)
        # highlight(
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
         # highlight((sketchText.boundingBox.minPoint, sketchText.boundingBox.maxPoint))
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






def getAllSheetBodiesFromSketch(sketch : adsk.fusion.Sketch) -> Sequence[adsk.fusion.BRepBody]:
    """ returns a sequence of BRepBody, containing one member for each member of sketch.profiles and 
    sheet bodies corresponding to the sketch texts. 
    each body is a sheet body having exactly one face."""
    #TODO: allow control over how we deal with overlapping profiles (which
    #generally happens in the case of nested loops).  For instance, we might
    #want to return only "odd-rank" faces.
    bodies = []

    ## FIRST ATTEMPT - construct the bodies "from scratch" by extracting the primitive entities from sketch.profiles.
    ## foiled due to missing functionality in fusion api.  Also foiled for SketchText objects that SketchText doesn't show up in sketch.profiles.
        # # profile : adsk.fusion.Profile
        # # for profile in sketch.profiles: 
        # #     bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()
        # #     brepLumpDefinition  = bRepBodyDefinition.lumpDefinitions.add()
        # #     brepShellDefinition = brepLumpDefinition.shellDefinitions.add()
        # #     brepFaceDefinition  = brepShellDefinition.faceDefinitions.add(
        # #         surfaceGeometry=profile.plane, 
        # #         isParamReversed=False
        # #         )

        # #     loop: adsk.fusion.ProfileLoop
        # #     for loop in profile.profileLoops:
        # #         bRepLoopDefinition = brepFaceDefinition.loopDefinitions.add()

                
                
        # #         edgeDefinitions = []
        # #         profileCurve : adsk.fusion.ProfileCurve
        # #         for profileCurve in loop.profileCurves:
                    
        # #             # in order to make edgeDefinitions, we need to have vertexDefinitions.
        # #             # There is no good way to construct all the vertexDefinitions (in general) because
        # #             # we some of our vertexDefinitions might need to correspond to the intersection of sketch curves, rather
        # #             # than their endpoints.
        # #             # therefore, we will have to generate a temporary body by means of TemporaryBrepManager::createWireFromCurves() and 
        # #             #  TemporaryBrepManager::createFaceFromPlanarWires()


                    
        # #             edgeDefinition = bRepBodyDefinition.createEdgeDefinitionByCurve(
        # #                 startVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.startVertex.tempId],
        # #                 endVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.endVertex.tempId],
        # #                 modelSpaceCurve=profileCurve.geometry
        # #             )
                    
        # #             edgeDefinitions.append(
        # #                 profileCurve.
        # #             )


        # #         for coEdgeLikeThing in collectionOfSuchThings:
        # #             bRepCoEdgeDefinition = bRepLoopDefinition.bRepCoEdgeDefinitions.add(
        # #                 edgeDefinition= , #construct an edgeDefinition object corresponding to coEdgeLikeThing
        # #                 isOpposedToEdge= # Set the isOpposedToEdge property according to some property of coEdgeLikeThing
        # #             )

        # #     bodies.append(bRepBodyDefinition.createBody())  
    
    # It seems to be prohibitively difficult to construct the bodies "from
    ## scratch" by extracting the primitive geometry from the profiles (because
    ## adsk.fusion.Profile doesn't quite expose enough of the underlying geometry
    ## to reliably handle all cases (for instance: vertices that are formed by
    ## the intersection of two sketch curves, not on the endpoints of the curve.)
    ## Therefore, we will do some fusion feature (probably, Extrude.  could
    ## possibly also use a Patch feature) that takes sketch profiles as input,
    ## and extract the needed geometry from the resultant bodies.

    ## SECOND ATTEMPT -- do a single Extrude feature and pass the collection of profiles as input.
    # foiled due to the fact that the fusion extrude feature 
    # automatically merges adjacent profiles, 
    # but we want to preserve the profiles as is.
        # # extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
        # #     profile= fscad._collection_of(sketch.profiles),
        # #     distance = adsk.core.ValueInput.createByReal(1),
        # #     operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        # # )
        # # bodies += [
        # #     fscad.brep().copy(face)
        # #     for face in extrudeFeature.startFaces
        # # ]


    ## THIRD ATTEMPT -- do one Extrude feature for each profile and each SketchText.
    profile : Union[adsk.fusion.Profile, adsk.fusion.SketchText]
    # Besides SketchText objects and Profile objects, are there any other profile-like objects
    # that can be contained in a sketch that we should think about handling?
    for profile in itertools.chain(sketch.profiles, sketch.sketchTexts): 
        # this extrude feature throws an exception in the case where profile is
        # a sketchtext such that profile.text == '', or even where profile.text
        # == ' ' (i.e. cases where the sketch text does not produce any "ink").
        # Precisely what is wrong with extruding an empty region?  It simply
        # yields an empty body. There's nothing ambiguous or problematic about
        # it. This seems to me no reason for the software to get all hoo-hooed.
        # how can we handle this situation gracefully.  Obviously, the correct
        # outcome is to add no items to bodies on this pass through the loop.
        # the question is not so much how to handle  the situation -- that's
        # easy - just don't attempt the extrusion operation and don't add
        # anything to bodies. the real question is how do we detect an "empty"
        # (i.e. zero ink) sketch-text. options:
        # - try the extrusion and look for exceptions.  The problem is that I am
        #   not sure this is a very specific test (although it is sensitive).
        # - inspect profile.boundingBox.  Unfortunately, in the case of a zero
        #   ink sketch text, the bounding box does not have any zero dimensions
        #   (small - 10 microns, perhaps, but not reliably zero)
        # - inspect len(profile.asCurves() ) (winner)
        
        if isinstance(profile, adsk.fusion.SketchText) and len(profile.asCurves()) == 0: continue
        
        extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
            profile= profile,
            distance = adsk.core.ValueInput.createByReal(-1),
            # it is important that this be negative 1 so that the faces have normals 
            # pointing in the same direction as the sketch's normal.
            operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        


        bodies += [
            fscad.brep().copy(face)
            for face in extrudeFeature.startFaces
        ]
        # In the case where profile is a single SketchProfile, I expect that
        # extrudeFeature.startFaces will always have just one face.  However,
        # this will not generally be true for the case where profile is a
        # SketchText. 
        
        extrudeFeature.deleteMe()


    return bodies