from typing import Optional, Sequence, Union
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
    
        #self.bitProtrusionY = 10 * millimeter;
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
        self.bitHolder : BitHolder = BitHolder()
        self.bitHolder.segments = [self]
        # as a side effect of the above, 
        # self.bitHolder will be set to dummyBitHolder.

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
        
        boxOccurrence = mainComponent.create_occurrence()
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
        print('len(edgesOfInterest): ' + str(len(edgesOfInterest)))


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
        

        boxOccurrence.deleteMe()
        TextRow(
            fontName="Times New Roman"

        ).create_occurrence()


        a = adsk.core.Point2D.create(11,22)
        b = adsk.core.Point3D.cast(a)

        # myGalley = Galley()
        # myGalley.fontName = self.labelFontName
        # myGalley.rowSpacing = 1.3
        # myGalley.rowHeight = self.labelFontHeight
        # myGalley.text = self.labelText
        # myGalley.horizontalAlignment = HorizontalAlignment.CENTER
        # myGalley.verticalAlignment = VerticalAlignment.TOP
        # myGalley.clipping = True
        # myGalley.width = self.labelExtentX
        # myGalley.height = self.labelExtentZ
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
        
        # // sculpt (i.e. either emboss or engrave, according to self.label.sculptingStrategy) the label tool onto the main body.
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


def castTo3dArray(x: Union[ndarray, adsk.core.Point3D, adsk.core.Point2D]) -> NDArray: #need to figure out how to use the shape-specificatin facility that I think is part of the NDArray type alias.
    if isinstance(x, ndarray):
        return x
        #TODO: handle various sizes of NDArray rather than blindly assuming that we have been given a 3-array
    elif isinstance(x, adsk.core.Point3D):
        return np.array(x.asArray()) 

def castToPoint3d(x: Union[ndarray, adsk.core.Point3D, adsk.core.Point2D]) -> adsk.core.Point3D:
    if isinstance(x, ndarray):
        return adsk.core.Point3D.create(*x)
        #TODO: handle various sizes of NDArray rather than blindly assuming that we have been given a 3-array
    elif isinstance(x, adsk.core.Point3D):
        return x
    elif isinstance(x, adsk.core.Point2D):
        return adsk.core.Point3D.create(x.x, x.y, 0)

class FilledRectangle:
    """ at the moment, FilledRectangle is jsut a factory for creating an fscad.PlanarShape object"""

    def __init__(self, corner1 = None, corner2 = None):
       
        self.corner1 = castTo3dArray((corner1 if corner1 is not None else vector(0,0,0) * meter))
        self.corner2 = castTo3dArray((corner2 if corner2 is not None else vector(1,1,0) * meter))
        
    # //this function constructs (And returns a query for) one sheet body, all lying on the xy plane.
    # //returns Query that resolves to a set of sheet bodies (or possibly a single sheet body with multiple disjoint faces, if such a thing is allowed), all lying on the xy plane.
    # returns an array of brep body with one element, that is a sheet body having but one face, namely a rectangular region lying in the xy plane
    def buildSheetBodiesInGalleySpace(self) -> fscad.PlanarShape:
        vertices = [
            vector(self.corner1[0] , self.corner1[1] , zeroLength),
            vector(self.corner2[0] , self.corner1[1] , zeroLength),
            vector(self.corner2[0] , self.corner2[1] , zeroLength),
            vector(self.corner1[0] , self.corner2[1] , zeroLength)
        ]

        # reverse the vertices if needed to ensure that the normal 
        # of the face will point in the z positive direction:
        if (self.corner1[0] < self.corner2[0]) != (self.corner1[1] < self.corner2[1]):
            vertices.reverse()
           
        
        polygon = fscad.Polygon(
            *itertools.starmap(
                adsk.core.Point3D.create,
                vertices
            )
        )

        return polygon

        # //debug(context, qConstructionFilter(qCreatedBy(idOfWorkingSketch, EntityType.EDGE), ConstructionObject.YES));

        # var idOfBodyCopy = id + "bodyCopy";
        
        # # //opPattern creates copies of the specified bodies.
        # # // we want to create a copy of the sheetBodies in the sketch, so that we have a copy, which is independent of the original sketch, so that we can then delete the sketch and be left with just the faces.
        
        # # //qSketchRegion returns all faces of all sheetBodies in the sketch if the second argument (filterInnerLoops) is false, or else the all the 'outer' faces of all sheetBodies in the sketch if filterInnerLoops is true.
        # var inkSheets is Query = qBodyType( qEntityFilter( qOwnerBody(qSketchRegion(idOfWorkingSketch,false)), EntityType.BODY), BodyType.SHEET) ;  //I realize that some of these filters are probably redundant - I just want to be darn sure that I am picking out exactly what I want (namely all sheetBodies in the sketch) and nothing else.
        
        # # //println("reportOnEntities(context,inkSheets,0): " ~ toString(reportOnEntities(context,inkSheets,0)));
        # # //debug(context, sheetBodiesInGalleySpace);
        
        
        # //delete all the even-rank faces (this concept of ranking of faces of a planar sheetBody is my own terminology -- not from the OnShape documentation.)
        # deleteEvenRankFaces(context, id + "deleteEvenRankFaces", inkSheets); //probably not strictly necessary in the case of a simple rectangle.
        
        # try silent{ 
        #     opPattern(context, idOfBodyCopy,
        #         {
        #             entities: inkSheets, 
        #             transforms: [ identityTransform()],
        #         //transforms: [ transform(vector(0,-3,0) * meter)], //for debugging.
        #             instanceNames: [uniqueIdString(context)]
        #         }
        #     );
        # } 

        # var scaleFreeSheetBodies = qBodyType(qEntityFilter(qCreatedBy(idOfBodyCopy), EntityType.BODY), BodyType.SHEET);   
        
        
        # # //print(reportOnEntities(context, inkSheets,0,0));
        # # //debug(context, inkSheets);
        # # //debug(context, qCreatedBy(idOfBodyCopy));
        
        # # //debug(context, qCreatedBy(idOfWorkingSketch));
        
        # # //get rid of all the entities in the sketch, which we do not need now that we have extracted the sheetBodies that we care about.
        # try silent{opDeleteBodies(
        #     context,
        #     uniqueId(context, id),
        #     {entities:qCreatedBy(idOfWorkingSketch)}
        # );  } 
        # # //println("reportOnEntities(context,scaleFreeSheetBodies,0): " ~ toString(reportOnEntities(context,scaleFreeSheetBodies,0)));
        # return scaleFreeSheetBodies;


class Galley(fscad.BRepComponent):
    def __init__(self, *args, **kwargs):
        super().init(*args, **kwargs)

class TextRow(fscad.BRepComponent):
    # todo: make all the properties read-only
    # a textrow is intended to be immutable.
    def __init__(self, 
        owningGalley : Optional[Galley] = None,
        text : str = "",
        fontName : str = "Arial", #"Tinos-Italic.ttf",
        characterHeight : float = 1 * inch,
        basePoint = vector(0,0,0) * meter,
        name: str = None
    ):
        self.owningGalley : Optional[Galley] = owningGalley 
        self.text = text
        self.fontName = fontName
        self.characterHeight = characterHeight 
        self.basePoint = basePoint 
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

        sheetBodies = [body.brep for body in FilledRectangle().buildSheetBodiesInGalleySpace().bodies]

        tempOccurrence = fscad._create_component(
            parent_component = fscad.root(), 
            name="temp"
        )
        sketch = tempOccurrence.component.sketches.add(tempOccurrence.component.xYConstructionPlane, tempOccurrence)

        sketchTextInput = sketch.sketchTexts.createInput2(
            formattedText="text",
            height=self.characterHeight
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


        sketchTextInput.fontName = self.fontName
        sketchTextInput.isHorizontalFlip = False
        sketchTextInput.isVerticalFlip = False
        sketchTextInput.textStyle = (
              0*adsk.fusion.TextStyles.TextStyleBold 
            + 0*adsk.fusion.TextStyles.TextStyleItalic 
            + 0*adsk.fusion.TextStyles.TextStyleUnderline
        )
        sketchText = sketch.sketchTexts.add(sketchTextInput)

        self.width = sketchText.boundingBox.maxPoint.x
        self.opticalDepth = min(0, -sketchText.boundingBox.minPoint.y)
        self.opticalHeight = max(0, sketchText.boundingBox.maxPoint.y)
                
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

        sheetBodies = getAllSheetBodiesFromSketch(sketch)
        tempOccurrence.deleteMe()
        super().__init__(
            *sheetBodies,
            component = None, 
            name = name
        )


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
        extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
            profile= profile,
            distance = adsk.core.ValueInput.createByReal(1),
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