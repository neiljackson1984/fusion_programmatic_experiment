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
        highlight(edgesOfInterest)
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
        

        # var myGalley = new_galley();
        # myGalley.fontName = self.labelFontName;
        # myGalley.rowSpacing = 1.3; 
        # myGalley.rowHeight = self.labelFontHeight;
        # myGalley.text = self.labelText;
        # myGalley.horizontalAlignment = HorizontalAlignment.CENTER;
        # myGalley.verticalAlignment = VerticalAlignment.TOP;
        # myGalley.clipping = true;
        # myGalley.width = self.labelExtentX;
        # myGalley.height = self.labelExtentZ;

        # myGalley.anchor = GalleyAnchor_e.CENTER;
        # myGalley.worldPlane = 
        #     plane(
        #         /* origin: */ vector(
        #             mean([self.labelXMin, self.labelXMax]),
        #             self.labelYMin, 
        #             mean([self.labelZMin, self.labelZMax])
        #         ),
        #         /* normal: */ -yHat,
        #         /* x direction: */ xHat  
        #     );
        # var sheetBodiesInWorld = myGalley.buildSheetBodiesInWorld(context, uniqueId(context,id));
        
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


class Galley:
    def __init__(self):

        self.width = 8.5 * inch
        self.height = 11 * inch
        self.clipping = True
        # this parameter controls whether to delete parts of the sheet bodies that extend beyond the galley boundary (determined by the width and height parameters above).  In galleySpace (the frame that is fixed to the galley) (the lower left corner of the galley is the origin).
        
        
        self.fontName = "Tinos-Regular.ttf"
        self.rowHeight = 10/72 * inch
        self.rowSpacing = 1
        #this is a unitless ratio that sets the ratio of the vertical interval between successive textRows and the rowHeight.
        
        self.horizontalAlignment = HorizontalAlignment.LEFT
        self.verticalAlignment = VerticalAlignment.TOP
        
        self.leftMargin    = zeroLength
        self.rightMargin   = zeroLength
        self.topMargin     = zeroLength
        self.bottomMargin  = zeroLength
        
        self.worldPlane = XY_PLANE; 
        
        # //the anchor specifies which point in galley space will be mapped to the origin of worldPlane.
        # // self.anchor may be any of the following:
        # //  a galleyAnchor_e enum value
        # //  a 3d length vector (according to is3dLengthVector()), in which case this will be taken as the point in galley space to be mapped to the origin of worldPlane
        # //  a unitless vector having at least 2 elements (Accordng to size() >= 2 and isUnitlessVector()), in which case the elements of self.anchor will taken to be a scale factor to be applied to width and height, respectively (in the spirit of the scaled position that Mathematica uses for many of its graphics functions)
        self.anchor = GalleyAnchor_e.BOTTOM_LEFT; 
        
        # //the text boxes will be aligned with the margin (which is a rectangular region that is inset from the edges of the galley according to the margin values above.

        self.text = ""
        # // self.fontName = "Tinos-Italic.ttf"
        # // self.fontHeight = 12/72 * inch

        
    def buildSheetBodiesInGalleySpace(context is Context, id is Id):
        var sanitizedText = "";
        //parse tex-style directives from the text.
        var regExForTexDirective = "(.*?)(?:\\\\(\\w+)(?:\\{(.*?)\\}|))(.*)";
        var texDirectives = [];
        var remainder = self.text;
        var result = match(remainder, regExForTexDirective) ;
        //println("result: " ~ toString(result));		// 
        while(result.hasMatch)
        {
            sanitizedText ~= result.captures[1];
            texDirectives =  append(texDirectives, 
                {
                    "controlWord" : result.captures[2],
                    "argument" : result.captures[3]
                }
            );
            remainder = result.captures[4];
            result = match(remainder, regExForTexDirective) ;
            //println("result: " ~ toString(result));		// 
        }
        sanitizedText ~= remainder;
        //println("regExForTexDirective: " ~ toString(regExForTexDirective));		// 
        //println("texDirectives: " ~ toString(texDirectives));		// 
        //println("sanitizedText: " ~ toString(sanitizedText));		// 
        var floodWithInk = false;
        if(
            isIn(
                "floodWithInk",
                mapArray(texDirectives,
                    function(x){return x["controlWord"];}
                )
            )
        )
        {
            //println("floodWithInk directive detected");  
            floodWithInk= true;
        }
        
        
        
        var sheetBodiesInGalleySpace = qNothing(); 
        //we will use sheetBodiesInGalleySpace as a container, which we willl fill up with sheet bodies.
        //By the time we are done working, sheetBodiesInGalleySpace will contain all the the sheetBodies that we want.
        
        if(floodWithInk)
        {
            sheetBodiesInGalleySpace = 
                qUnion([
                    sheetBodiesInGalleySpace,
                    // rectangle from [0,0] to [self.width, self.height]  //thisTextRow[].buildSheetBodiesInGalleySpace(context, uniqueId(context, id))
                    new_filledRectangle({"corner1": vector(0,0) * meter, "corner2": vector(self.width, self.height)})[].buildSheetBodiesInGalleySpace(context, uniqueId(context, id))
                ]);
            //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
        } else {
            // lay down the text boxes
            { 
                var linesOfText = explode("\n", sanitizedText);
                var initX;
                var initY;
                var initZ = zeroLength;
                
                                    
                //the following tthree lines allow the fontName, rowHeight, and rowSpacing to be either arrays or single values.
                // if an array, we will cycle through the values in the array as we create one row after another.
                var fontNameArray = (self.fontName is array ? self.fontName : [self.fontName]);
                var rowHeightArray = (self.rowHeight is array ? self.rowHeight : [self.rowHeight]);
                var rowSpacingArray = (self.rowSpacing is array ? self.rowSpacing : [self.rowSpacing]); // the entries in the row spacing array affect how much space will exist between a row and the row above it. (thus, row spacing for the first row has no effect - only for rows after the first row.)
                
                //verticalRowInterval is the vertical distance that we will move the insertion point between successive rows.
                //var verticalRowInterval = self.rowHeight * self.rowSpacing; 
                
                
                //heightOfAllText is the distance from the baseline of the bottom row to the ascent of the top row, when all rows are laid out.
                //var heightOfAllText = verticalRowInterval * size(linesOfText);
                var heightOfAllText = rowHeightArray[0];
                for(var i = 1; i<size(linesOfText); i+=1)
                {
                    //self.rowHeight + (size(linesOfText)-1)*verticalRowInterval;
                    heightOfAllText += rowSpacingArray[i % size(rowSpacingArray)] * rowHeightArray[i % size(rowHeightArray)];
                }
                
                if(  self.horizontalAlignment == HorizontalAlignment.LEFT )
                {
                    initX = self.leftMargin;
                } else if (self.horizontalAlignment == HorizontalAlignment.CENTER)
                {
                    initX = mean([ self.leftMargin, self.width - self.rightMargin ]);
                }
                else // if (self.horizontalAlignment == HorizontalAlignment.RIGHT)
                {
                    initX = self.width - self.rightMargin;
                }
                
                
                
                if(  self.verticalAlignment == VerticalAlignment.TOP )
                {
                    initY = self.height - self.topMargin - rowHeightArray[0];
                } else if (self.verticalAlignment == VerticalAlignment.CENTER)
                {
                    initY = 
                        mean([self.height - self.topMargin, self.bottomMargin]) //this is the y-coordinate of the vertical center
                        + heightOfAllText/2 
                        - self.rowHeight;
                }
                else // if(  self.verticalAlignment == VerticalAlignment.BOTTOM )
                {
                    initY = self.bottomMargin + heightOfAllText - rowHeightArray[0];
                }
                
                var insertionPoint = vector(initX, initY , initZ);

                
                for(var i = 0; i<size(linesOfText); i+=1)
                {
                    var lineOfText = linesOfText[i];
                    var thisTextRow =  new_textRow()  ;
                    
                    thisTextRow[].set_owningGalley(this);
                    thisTextRow[].set_text(lineOfText);
                    thisTextRow[].set_fontName(fontNameArray[i % size(fontNameArray)]);
                    thisTextRow[].set_height(rowHeightArray[i % size(rowHeightArray)]);
                    
                    
                    if(  self.horizontalAlignment == HorizontalAlignment.LEFT )
                    {
                            thisTextRow[].set_basePoint(insertionPoint);
                    } else if (self.horizontalAlignment == HorizontalAlignment.CENTER)
                    {
                            thisTextRow[].set_basePoint(insertionPoint - thisTextRow.width/2 * vector(1, 0, 0));
                    }
                    else // if(  self.horizontalAlignment == HorizontalAlignment.RIGHT )
                    {
                        thisTextRow[].set_basePoint(insertionPoint - thisTextRow.width * vector(1, 0, 0));
                    }
                    
                    if(i<size(linesOfText)-1) //if we are not on the last row
                    {
                        insertionPoint += -yHat * rowSpacingArray[i+1 % size(rowSpacingArray)] * rowHeightArray[i+1 % size(rowHeightArray)]; //drop the insertion point down to be ready to start the next row.
                    }
                    
                    
                    
                    sheetBodiesInGalleySpace = 
                        qUnion([
                            sheetBodiesInGalleySpace,
                            thisTextRow[].buildSheetBodiesInGalleySpace(context, uniqueId(context, id))
                        ]);
                }
            }
        }
        //apply clipping, if requested.
        if(self.clipping)
        {
            
            var idOfGalleyMask = uniqueId(context, id);
            var idOfClipping = uniqueId(context, id);                
            var idOfTextExtrude = uniqueId(context, id);
            //construct the galleyMask.  This is a region outside of which we will not allow the galley to have any effect.  
            // (We will do a boolean intersection between galleyMask and the sheet bodies created above.
            
            fCuboid(
                context,
                idOfGalleyMask,
                {
                    corner1:vector(0,0,-1) * millimeter,
                    corner2:vector(self.width , self.height , 1 * millimeter)
                }
            );
            var galleyMask = qCreatedBy(idOfGalleyMask, EntityType.BODY);
            //println("reportOnEntities(context,galleyMask,0): " ~ toString(reportOnEntities(context,galleyMask,0)));
            //debug(context, qOwnedByBody(sheetBodiesInGalleySpace, EntityType.FACE));
            try{
                opExtrude(
                    context,
                    idOfTextExtrude,
                    {
                        //entities:  sheetBodiesInGalleySpace,
                        entities:  qOwnedByBody(sheetBodiesInGalleySpace, EntityType.FACE),
                        direction: vector(0,0,1),
                        endBound: BoundingType.BLIND,
                        endDepth: 0.5 * millimeter,
                        startBound: BoundingType.BLIND,
                        startDepth: zeroLength
                    }
                );
            } catch (error)
            {
                println("getFeatureError(context, idOfTextExtrude): " ~ getFeatureError(context, idOfTextExtrude));		// getFeatureError(context, idOfTextExtrude);
            }
            
            
            
            var textSolidBodies = qBodyType(qCreatedBy(idOfTextExtrude, EntityType.BODY), BodyType.SOLID);
            //debug(context, textSolidBodies);                    
            //debug(context, sheetBodiesInGalleySpace);
            //debug(context, galleyMask);
            //println("before clipping: reportOnEntities(context, textSolidBodies): " ~ reportOnEntities(context, textSolidBodies,0,0));		
            //println("before clipping: reportOnEntities(context, galleyMask): " ~ reportOnEntities(context, galleyMask,0,0));
            
            if(false){ //This doesn't work because the boolean intersection completely ignores the "targets" argument.
                // It acts only on the tools.
                opBoolean(context, idOfClipping,
                    {
                        tools: galleyMask,
                        targets: textSolidBodies,
                        ////targets: sheetBodiesInGalleySpace,
                        operationType: BooleanOperationType.INTERSECTION,
                        targetsAndToolsNeedGrouping:true,
                        keepTools:true
                    }
                ); 
            }
            
            
            opBoolean(
                context,
                idOfClipping,
                {
                    tools: galleyMask,
                    targets: textSolidBodies,
                    //targets: sheetBodiesInGalleySpace,
                    operationType: BooleanOperationType.SUBTRACT_COMPLEMENT,
                    targetsAndToolsNeedGrouping:false,
                    keepTools:false
                }
            );
            // // Counter-intuitively, the boolean SUBTRACT_COMPLEMENT operation (which relies on the boolean SUBTRACT operation 
            // // under the hood,
            // // and therefore this is probably also true for the SUBTRACT operation) essentially destroys all input bodies 
            // // and creates brand new bodies.  Therefore, we need to redefine the textSoidBodies query
            // // to be the set of solid bodies created by the clipping operation:
            // // textSolidBodies = qBodyType(qCreatedBy(idOfClipping, EntityType.BODY), BodyType.SOLID);
            // UPDATE: after updating from Featurescript version 626 to version 1271,
            // it seems that the boolean SUBTRAC_COMPLEMENT operation (and, presumably also the SUBTRACT operation)
            // now behaves intuitively and does not destroy all input bodies.  Therefore, it is no longer necessary
            // to redefine the textSolidBodies query to be the set of solid boides created by the clipping operation.
            // In fact, if we did now perform that re-definition, the newly defined textSolidBodies query would 
            // resolve to nothing, because the new version of the SUBTRACt_COMPLEMENT operation does not 'create' any solid
            // bodies - it merely modifies them.  (although perhaps it does create edges and faces where existing solid bodies are chopped
            // up.
    
            

            
            
            
            
            //println("after clipping: reportOnEntities(context, textSolidBodies): " ~ reportOnEntities(context, textSolidBodies,0,0));		
            //println("after clipping: reportOnEntities(context, galleyMask): " ~ reportOnEntities(context, galleyMask,0,0));
            //debug(context, qOwnedByBody(textSolidBodies, EntityType.EDGE));  
            var allFacesOfTextSolidBodies = qOwnedByBody(textSolidBodies,EntityType.FACE);
            var facesToKeep = qCoincidesWithPlane(allFacesOfTextSolidBodies, XY_PLANE);
            var facesToDelete = qSubtraction(allFacesOfTextSolidBodies, facesToKeep);
            var newEntitiesFromDeleteFace = startTracking(context, qUnion([textSolidBodies, allFacesOfTextSolidBodies]));
            
            //delete faces from allFacesOfTextSolidBodies that do not lie on the XY plane
            var idOfDeleteFace = uniqueId(context, id);
            try silent{
                opDeleteFace(
                    context,
                    idOfDeleteFace,
                    {
                        deleteFaces: facesToDelete ,
                        includeFillet:false,
                        capVoid:false,
                        leaveOpen:true
                    }
                );
                // this opDeleteFace will throw an excpetion when facesToDelete is empty (which happens when all the textSolidBodies lie entirely outside the galley mask.  That is the reason for the try{}.
                
            } catch(error)
            {
                
            }
            //by deleting faces, the solid bodies will have become sheet bodies.
            // the opDeleteFace operation doesn't "create" any bodies (in the sense of OnShape id assignment), however it does seem to destroy all input bodies (at least in this case, where we are removing faces from a solid body to end up with a sheet body).  The only way I have found to retrieve the resultant sheet bodies is with a tracking query.  
            var clippedSheetBodiesInGalleySpace =
                qBodyType(
                    qOwnerBody(
                        qEntityFilter(newEntitiesFromDeleteFace,EntityType.FACE)
                    ), 
                    BodyType.SHEET
                );
            
            //Not knowing exactly how the tracking query works, I am running the query through evaluateQuery() here for good measure, to make sure that I can use this query later on to still refer to preciesly the entities which exist at this point in the build history.            
            clippedSheetBodiesInGalleySpace = qUnion(evaluateQuery(context, clippedSheetBodiesInGalleySpace));

            if(false){
                println("reportOnEntities(context, qCreatedBy(idOfDeleteFace),1,0): "      ~ "\n" ~ reportOnEntities(context, qCreatedBy(idOfDeleteFace),   1, 0));	
                println("reportOnEntities(context, textSolidBodies,1,0): "                 ~ "\n" ~ reportOnEntities(context, textSolidBodies,              1, 0));	
                println("reportOnEntities(context, facesToKeep,1,0): "                     ~ "\n" ~ reportOnEntities(context, facesToKeep,                  1, 0));	
                println("reportOnEntities(context, newEntitiesFromDeleteFace,0,0): "       ~ "\n" ~ reportOnEntities(context, newEntitiesFromDeleteFace,    1, 0));	
                println("reportOnEntities(context, clippedSheetBodiesInGalleySpace, 1, 0): "      ~ "\n" ~ reportOnEntities(context, clippedSheetBodiesInGalleySpace,     1, 0)); 
                //debug(context,clippedSheetBodiesInGalleySpace);
                //debug(context,sheetBodiesInGalleySpace);
            }
            
            //delete the original sheetBodiesInGalleySpace, and set sheetBodiesInGalleySpace = clippedSheetBodiesInGalleySpace
            opDeleteBodies(context, uniqueId(context, id),{entities: sheetBodiesInGalleySpace});
            sheetBodiesInGalleySpace = clippedSheetBodiesInGalleySpace;
    
            
            
        }
        //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
            return sheetBodiesInGalleySpace;
        
    
    def buildSheetBodiesInWorld(context is Context, id is Id):
        var sheetBodiesInWorld = qNothing(); 
        var scaledAnchorPoint;
        
        //anchorPointInGalleySpace is the point in galley space that will be mapped to the origin of worldPlane.
        var anchorPointInGalleySpace;
        // compute anchorPointInGalleySpace. 
        if (is3dLengthVector(self.anchor))
        {
            anchorPointInGalleySpace =  self.anchor;
        } else
        {            
            //compute scaledAnchorPoint, one way or another.
            if (isUnitlessVector(self.anchor) && size(self.anchor) >= 2)
            {
                scaledAnchorPoint = resize(self.anchor, 3, 0); //doing this resize lets us take an anchor that only gives x and y coordinates
            } else if(self.anchor is galleyAnchor_e)
            {
                scaledAnchorPoint  = 
                    {
                        GalleyAnchor_e.TOP_LEFT:         vector(  0,    1,    0  ),     
                        GalleyAnchor_e.TOP_CENTER:       vector(  1/2,  1,    0  ),     
                        GalleyAnchor_e.TOP_RIGHT:        vector(  1,    1,    0  ),
                        GalleyAnchor_e.CENTER_LEFT:      vector(  0,    1/2,  0  ),  
                        GalleyAnchor_e.CENTER:           vector(  1/2,  1/2,  0  ),         
                        GalleyAnchor_e.CENTER_RIGHT:     vector(  1,    1/2,  0  ),
                        GalleyAnchor_e.BOTTOM_LEFT:      vector(  0,    0,    0  ),  
                        GalleyAnchor_e.BOTTOM_CENTER:    vector(  1/2,  0,    0  ),  
                        GalleyAnchor_e.BOTTOM_RIGHT:     vector(  1,    0,    0  )
                    }[self.anchor];
                } else {
                throw ("anchor was neither a 3dLengthVector, nor a unitless vector containing at least two elements, nor a galleyAnchor_e enum value.");    
                }
                //at this point, scaledAnchorPoint is computed.
                anchorPointInGalleySpace = elementWiseProduct(scaledAnchorPoint, vector(self.width, self.height, zeroLength));
        }

        //println("anchorPointInGalleySpace: " ~ toString(anchorPointInGalleySpace));		// anchorPointInGalleySpace
        
        
        var sheetBodiesInGalleySpace = self.buildSheetBodiesInGalleySpace(context, uniqueId(context, id));
        //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
        //debug(context, sheetBodiesInGalleySpace);
        opTransform(
            context, 
            uniqueId(context, id), 
            {
                "bodies": sheetBodiesInGalleySpace,
                "transform": transform(XY_PLANE, self.worldPlane) * transform(-anchorPointInGalleySpace)
            }
        );
        sheetBodiesInWorld = sheetBodiesInGalleySpace;
        //debug(context, sheetBodiesInWorld);
        //println("reportOnEntities(context,sheetBodiesInWorld,0,0): " ~ toString(reportOnEntities(context,sheetBodiesInWorld,0,0)));		// reportOnEntities(context,sheetBodiesInWorld,0,0);
        return sheetBodiesInWorld;

class TextRow:
    def __init__(self):
        # var this is box = new box({});
        # var private is box =  new box({}); //this stores private members
        

        self.height = 1 * inch #//isLength ///when we go to create sheet bodies on the galley, we will look at this value and scale the size of the bodies accordingly.  We will scale the size of the bodies so that the nominal height of the text (as would be measured from the automatically-gnerated cotruction line segmens that an OnShape sketchText sketch entity generates.) will become self.fontHeight.
        self.basePoint = vector(0,0,0) * meter #; //is3dLengthVector  //this is a vector, in galleySpace (galleySpace is 3 dimensional, although only the x and y dimensions are significant for the final results. (When we are building bodies for a layout, we first create all the bodies "in galleySpace" and then transform them all by the galleyToWorld transform.  
        
        # // The following comment was written before I decided to use the name "galley".  Prior to 'galley', I was unsing the word "textLayout" to refer to galley.
        # //  (The 'paper' here is not to be confused with the 'paper' on which a 2d drawing of this 3d model might be drawn).  (I really need to come up with a better word than 'paper' for the current project, because "paper" is already used in the context of making 2d drawings.  Perhaps poster is a better word.  Broadside, banner, billboard, marquee, signboard, foil. lamina, saran wrap, plastic wrap, cling wrap, film, membrane, stratum, veneer, mat, varnish, skin, graphicSkin, veil, screen, facade, parchment, velum, fabric, leaf, inkMembrane, inkSpace, inkSheet, inkScape, placard, plaque, plate, proofPlate, blackboard, whiteboard, readerboard, engraving, galley (in the context of a printing press) - a galley is the tray into which a person would lay type (e.g. lead (Pb) type - think 'printing press') into and tighten the type into place.  This is exactly the notion I am after, and "galley" does not have any alternate uses in the context of 3d geomtric modeling.  The galley isn't really an solid object within the model - it is a tool that can be brought to bear on the model to make engraves in the solid of the model (or embosses - yes, that stretches the analogy a bit, but the concept is close enough), and then, when you are finished with the galley, you put it back in the drawer from whence it came.  In other words, the galley itself is not part of the final finsihed model, but the marks that the galley makes are part of the finished model.
        
        
        
        self._text = "" #; //this value can (and probably will be) changed later by the calling code (via self.set()).
        self._fontName = "Tinos-Italic.ttf" #; //this value can (and probably will be) changed later by the calling code (via self.set()).
        self._owningGalley = None #  //this will be set to a galley object when the time comes to add this textRow to a particular owning textLayout. 
        
        self._scaleFreeShapeParameters = ["scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"] #; //'depth' here is in the TeX sense of the word (depth is the amount by which the characeters protrude below the baseline)
        # // the members of scaleFreeShape are nuumbers with length units, but any one of these values is not significnt in itself -- what matters is the ratio between 
        # // and among pairs of 'scaleFree' dimensions.  These ratios describe the shape of the textRow irrespective of scale.
        

        self._shapeChangers = ["text", "fontName"];
        # // these are the names of properties of private[], which will, when changed, affect the scaleFreeShapeParameters.  We will allow the user to set these properties (via a setter function), 
        # // but the setter function will turn on the shapeIsDirty flag so that we will know that we need to recompute the shape if we want good shape data.
        
        
        self._shapeIsDirty = True
        # //this is a flag that we will set to true whenever any of the parameters designated in shapeChangers is set.
        
        
        self._getablePrivates = ["text", "fontName", "owningGalley", "scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"]; #//"width" is computed on demand from the scaleFreeShape and the fontHeight, which is the one parameter that 
        # //whenever the calling code uses self.set() to set a private member, if the name of the private member is in self._shapeChangers, we recompute the scaleFreeShapeParameters
        
    
    def _computeShape(self):
        self._buildScaleFreeSheetBodies(newContextWithDefaults(), makeId("dummyDummyDummy"))
        # //  As a side effect, self._buildScaleFreeSheetBodies() computes and sets the scale free shape parameters, so we merely have to let it run in a temporary dummy context.  We don't care about saving the results of the build in the temporary context, we are just getting the data we need and then letting the temporary context be destroyed by garbage collection. 

    
    
    # //this function constructs (And returns a query for) one or more sheet bodies, all lying on the xy plane.
    # // as a side effect, this function computes scaleFreeShapeParameters
    
    # //we are assuming that the sheet bodies will be positioned so that the basePoint of the row of text is at the origin, the 
    # // normal of the plane that the text is on points in the positive z direction, and the reading direction of 
    # //  the text points in the positive x direction.

    #returns Query that resolves to a set of sheet bodies (or possibly a single sheet body with multiple disjoint faces, if such a thing is allowed), all lying on the xy plane.
    def _buildScaleFreeSheetBodies(self, context is Context, id is Id): 
        var idOfWorkingSketch = id + "workingSketch";
        var workingSketch is Sketch = newSketchOnPlane(context, idOfWorkingSketch, {    "sketchPlane":XY_PLANE     });
        var sketchEntityIdOfSketchText = "neilsText";
        var textIdMap;
        try{  
        textIdMap = 
                skText(workingSketch, sketchEntityIdOfSketchText,
                    {
                        "text": self.get_text(),
                        "fontName": self.get_fontName(),
                    }
                );
            //println("textIdMap: " ~ textIdMap);
        } catch(error) {
            println("skText threw an excpetion.");   
        }
        try{skSolve(workingSketch);}
        //debug(context, qConstructionFilter(qCreatedBy(idOfWorkingSketch, EntityType.EDGE), ConstructionObject.YES));
        var mySketchTextData;
        try{mySketchTextData = getSketchTextData(context, idOfWorkingSketch, sketchEntityIdOfSketchText);}
        try{self._scaleFreeHeight = mySketchTextData.nominalHeight;}
        try{self._scaleFreeWidth = mySketchTextData.nominalWidth;}
        
        //println("mySketchTextData: " ~ mapToString(mySketchTextData));
        
        var idOfBodyCopy = id + "bodyCopy";
        
        //opPattern creates copies of the specified bodies.
        // we want to create a copy of the sheetBodies in the sketch, so that we have a copy, which is independent of the original sketch, so that we can then delete the sketch and be left with just the faces.
        
        //qSketchRegion returns all faces of all sheetBodies in the sketch if the second argument (filterInnerLoops) is false, or else the all the 'outer' faces of all sheetBodies in the sketch if filterInnerLoops is true.
        var inkSheets is Query = qBodyType( qEntityFilter( qOwnerBody(qSketchRegion(idOfWorkingSketch,false)), EntityType.BODY), BodyType.SHEET) ;  //I realize that some of these filters are probably redundant - I just want to be darn sure that I am picking out exactly what I want (namely all sheetBodies in the sketch) and nothing else.
        
        //delete all the even-rank faces (this concept of ranking of faces of a planar sheetBody is my own terminology -- not from the OnShape documentation.)
        deleteEvenRankFaces(context, id + "deleteEvenRankFaces", inkSheets);
        
        //To DO: use onshape ev... evaluation functions to find the actual bounding box of the glyphs.
        
        
        try silent{ 
            opPattern(context, idOfBodyCopy,
                {
                    entities: inkSheets, 
                    transforms: [ identityTransform()],
                //transforms: [ transform(vector(0,-3,0) * meter)], //for debugging.
                    instanceNames: [uniqueIdString(context)]
                }
            );
        } 

        var scaleFreeSheetBodies = qBodyType(qEntityFilter(qCreatedBy(idOfBodyCopy), EntityType.BODY), BodyType.SHEET);   
        
        
        //print(reportOnEntities(context, inkSheets,0,0));
        //debug(context, inkSheets);
        //debug(context, qCreatedBy(idOfBodyCopy));
        
        //debug(context, qCreatedBy(idOfWorkingSketch));
        
        //get rid of all the entities in the sketch, which we do not need now that we have extracted the sheetBodies that we care about.
        try silent{opDeleteBodies(
            context,
            uniqueId(context, id),
            {entities:qCreatedBy(idOfWorkingSketch)}
        );  } 
        
        
        self._shapeIsDirty = false;
        //debug(context, qCreatedBy(idOfWorkingSketch));
        return scaleFreeSheetBodies;

    
    
    # // builds the sheetBodies in galley space, returns the resulting sheetBodies
    def buildSheetBodiesInGalleySpace(self, context is Context, id is Id) = 
        var scaleFreeSheetBodies = self._buildScaleFreeSheetBodies(context, id + "buildScaleFreeSheetBodies");
        # //scale and translate and scaleFreeSheetBodies according to self.get("height") and self.get("basePoint")
        
        var idOfTransformOperation = "scaleFreeTextRowToGalley";

        try{
            opTransform(context, id + idOfTransformOperation,
                {
                    "bodies": scaleFreeSheetBodies,
                    "transform": transform(self.get_basePoint()) * scaleUniformly(self.get_height()/self.get_scaleFreeHeight())    
                }
            );
        }
        
        
        return scaleFreeSheetBodies;  // I am assuming the the query for the bodies still refers the (now transformed bodies).


    // create a getters and setters
    addDefaultGettersAndSetters(this);
    
    for(var propertyName in self._getablePrivates)
    {
        if(isIn(propertyName, self._scaleFreeShapeParameters))
        {
            this[]["get_" ~ propertyName] = 
            function(){
                //recompute the shape if the shape data is out of date ( self._computeShape() will clear the shapeIsDirty flag.)
                if(self._shapeIsDirty){self._computeShape();}
                return private[][propertyName];
            };   
        } else
        {
            this[]["get_" ~ propertyName] = function(){return private[][propertyName];};   
        }
    }
    
    this[]["get_" ~ "width"] = function(){
        return self.get_height() * self.get_scaleFreeWidth()/self.get_scaleFreeHeight();
        };
    
    
    for(var propertyName in self._shapeChangers)
    {
        this[]["set_" ~ propertyName] = 
            function(newValue)
            {
                private[][propertyName] = newValue;
                self._shapeIsDirty = true;
                return newValue;
            };
    }
    this[]["set_" ~ "owningGalley"] = function(newValue){private[]["owningGalley"] = newValue; return newValue;};

class FilledRectangle:
    def __init__(self):
        var this is box = new box({});
        var private is box =  new box({}); //this stores private members
        
        self.corner1 = vector(0,0) * meter;
        self.corner2 = vector(1,1) * meter;
        
    # //this function constructs (And returns a query for) one sheet body, all lying on the xy plane.
    # //returns Query that resolves to a set of sheet bodies (or possibly a single sheet body with multiple disjoint faces, if such a thing is allowed), all lying on the xy plane.
    def buildSheetBodiesInGalleySpace(self,context is Context, id is Id):
        var idOfWorkingSketch = id + "workingSketch";
        var workingSketch is Sketch = newSketchOnPlane(context, idOfWorkingSketch, {    "sketchPlane":XY_PLANE     });
        var sketchRectangleId = "neilsRectangle";
        try{  
        var result = 
                skRectangle(workingSketch, sketchRectangleId,
                    {
                        "firstCorner": self.get_corner1(),
                        "secondCorner": self.get_corner2(),
                        "construction": false,
                    }
                );
        } catch(error) {
            println("skRectangle threw an excpetion.");   
        }
        try{skSolve(workingSketch);}
        //debug(context, qConstructionFilter(qCreatedBy(idOfWorkingSketch, EntityType.EDGE), ConstructionObject.YES));

        var idOfBodyCopy = id + "bodyCopy";
        
        //opPattern creates copies of the specified bodies.
        // we want to create a copy of the sheetBodies in the sketch, so that we have a copy, which is independent of the original sketch, so that we can then delete the sketch and be left with just the faces.
        
        //qSketchRegion returns all faces of all sheetBodies in the sketch if the second argument (filterInnerLoops) is false, or else the all the 'outer' faces of all sheetBodies in the sketch if filterInnerLoops is true.
        var inkSheets is Query = qBodyType( qEntityFilter( qOwnerBody(qSketchRegion(idOfWorkingSketch,false)), EntityType.BODY), BodyType.SHEET) ;  //I realize that some of these filters are probably redundant - I just want to be darn sure that I am picking out exactly what I want (namely all sheetBodies in the sketch) and nothing else.
        
        //println("reportOnEntities(context,inkSheets,0): " ~ toString(reportOnEntities(context,inkSheets,0)));
        //debug(context, sheetBodiesInGalleySpace);
        
        
        //delete all the even-rank faces (this concept of ranking of faces of a planar sheetBody is my own terminology -- not from the OnShape documentation.)
        deleteEvenRankFaces(context, id + "deleteEvenRankFaces", inkSheets); //probably not strictly necessary in the case of a simple rectangle.
        
        try silent{ 
            opPattern(context, idOfBodyCopy,
                {
                    entities: inkSheets, 
                    transforms: [ identityTransform()],
                //transforms: [ transform(vector(0,-3,0) * meter)], //for debugging.
                    instanceNames: [uniqueIdString(context)]
                }
            );
        } 

        var scaleFreeSheetBodies = qBodyType(qEntityFilter(qCreatedBy(idOfBodyCopy), EntityType.BODY), BodyType.SHEET);   
        
        
        //print(reportOnEntities(context, inkSheets,0,0));
        //debug(context, inkSheets);
        //debug(context, qCreatedBy(idOfBodyCopy));
        
        //debug(context, qCreatedBy(idOfWorkingSketch));
        
        //get rid of all the entities in the sketch, which we do not need now that we have extracted the sheetBodies that we care about.
        try silent{opDeleteBodies(
            context,
            uniqueId(context, id),
            {entities:qCreatedBy(idOfWorkingSketch)}
        );  } 
        //println("reportOnEntities(context,scaleFreeSheetBodies,0): " ~ toString(reportOnEntities(context,scaleFreeSheetBodies,0)));
        return scaleFreeSheetBodies;

    // create a getters and setters
    addDefaultGettersAndSetters(this);
    

