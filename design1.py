import os, sys
import adsk.core, adsk.fusion, traceback
import inspect
import pprint
from typing import Optional, Sequence, Union
from . import scripted_component
from . import bit_holder
from .scripted_component import ScriptedComponent
from .bolt import Bolt
from .braids.fscad.src.fscad import fscad as fscad
from .highlight import *
import uuid
import traceback
import time

import pathlib
import itertools

def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent


def renderEntityToken(entityToken: str) -> str:
    # return "\n".join( entityToken.split('/'))
    import base64
    import string
    import zlib
    
    bb = base64.b64decode(entityToken)
    ss = []

    for i in range(len(bb)):
        # try:
        #     s = ba[i:i+1].decode('ascii')
        # except:
        #     s = ba[i:i+1].hex()

        if (
            bb[i] in string.printable.encode('ascii') 
            and not (bb[i] in "\t\r\n\x0b\x0c".encode('ascii'))
            and bb[i] != 255
            and False
        ) :
            s = bb[i:i+1].decode('ascii')
        else:
            s = bb[i:i+1].hex()
        ss.append(s)

    # zlib.decompress(bb[21:])

    return  "".join(ss)
    # + "\n" + "\n".join( 
    #     (
    #         str(len(piece)) + ' ' + piece
    #         for piece in entityToken.split('/')
    #     )
    
    # )
    return entityToken

def run(context:dict):
    
    if False:
        design = adsk.fusion.Design.cast(app().activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        rootComponent = design.rootComponent
        ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
        # print("ScriptedComponent.__subclasses__(): " + str(ScriptedComponent.__subclasses__()))

        pp=pprint.PrettyPrinter(indent=4, width=80, depth=2, compact=False); 
        # pp.pprint(
        #     inspect.getmembers(ScriptedComponent.__subclasses__()[0])
        # )
        # print(ScriptedComponent.__subclasses__()[0].__qualname__)
        # print(ScriptedComponent.__subclasses__()[0].__name__)


        if len(ScriptedComponent.getAllScriptedComponentsInAFusionDesign(design)) < 3:
            thisBolt = Bolt.create(design.rootComponent)
            # thisBolt.length += 1.0 * len(ScriptedComponent.getAllScriptedComponentsInAFusionDesign(design))
        return

    def design1():
        base_polygon = fscad.RegularPolygon(6, 1, is_outer_radius=False)
        box = fscad.Extrude(base_polygon, 2)

        # ball = fscad.Sphere(0.6, "ball")
        holeTool = fscad.Cylinder(height=2,radius=0.2)
        holeTool.rotate(rx=50).rotate(rz=84).translate(tz=1)
        # base = fscad.Difference(box, holeTool)

        # y = fscad.RegularPolygon(5, 3.2, is_outer_radius=False)

        # base = fscad.Group((base, y))
        # base = fscad.BRepComponent( *(fscadbody.brep for fscadbody in base.bodies ) )

        # mainOccurrence = base.create_occurrence(create_children=False, scale=1)
        
        ''' I would like to be able to pick out the edges within base adjacent
         to any face that was present in box, and that were newly created as a
         result of the Difference operation.  Thinking of the Difference
         operation as drilling a blind hole, the edges I am interested in are
         the "lip" of the hole. How can I pick out these edges? One idea is to,
         before doing the Difference, tag all of the faces and edges of box
         (with a tagging system that will preserve tags across body-modifying
         operations).  Then, after the difference operation, I pick out untagged
         edges of the tagged faces -- these have to be the newly-created edges
         that I am interested in. '''

        # adsk.fusion.BRepBody.findByTempId
        # adsk.fusion.Design.findEntityByToken

        # adsk.fusion.BRepEdge.tempId 
        ''' Returns the temporary ID of this edge. This ID is only good while
         the document remains open and as long as the owning BRepBody is not
         modified in any way. The findByTempId method of the BRepBody will
         return the entity in the body with the given ID. '''

        # adsk.fusion.BRepEdge.entityToken
        ''' Returns a token for the BRepEdge object. This can be saved and used
         at a later time with the Design.findEntityByToken method to get back
         the same edge. When using entity tokens it's important to understand
         that the token string returned for a specific entity can be different
         over time. However, even if you have two different token strings that
         were obtained from the same entity, when you use findEntityByToken they
         will both return the same entity. Because of that you should never
         compare entity tokens as way to determine what the token represents.
         Instead, you need to use the findEntityByToken method to get the two
         entities identified by the tokens and then compare them. This is only
         valid for edges that exist in the design, (the isTemporary property is
         false).'''

        ''' BRepFace  has the same tempId and entityToken properties.'''
        ##
         # edgesToHighlight : Sequence[fscad.Edge] = base.bodies[0].edges[0:2]
         # edgesToHighlight : Sequence[fscad.Edge] = base.bodies[0].edges
         # edgesToHighlight : Sequence[fscad.Edge] = base.edges
         # curvesToHighlight : Sequence[adsk.core.Curve3D] = [ x.brep.geometry for x in edgesToHighlight  ]
         # temporaryBRepManager : adsk.fusion.TemporaryBRepManager = adsk.fusion.TemporaryBRepManager.get()
         # (wireBodyToHighlight, edgeMap) = temporaryBRepManager.createWireFromCurves(curvesToHighlight)
         # print('bool(wireBodyToHighlight): ' + str(bool(wireBodyToHighlight)))
         # rootComponent = mainOccurrence.component.parentDesign.rootComponent

        # entitiesToHighlight : Sequence[HighlightableThing] = []
        # entitiesToHighlight += base.bodies[0].edges[1:2]

        # # goal: identify the lip edges
        # # Strategy 1: use fscad's 'named faces' system
        # box.add_named_faces('initialFaces', *box.faces) 
        # base = fscad.Difference(box, holeTool) 
        # entitiesToHighlight += base.named_faces('initialFaces') or [] 
        # ''' that doesn't work; face names do not appear to survive a difference
        #  operation (or,  because the difference operation does not so much
        #  modify its arguments as construct a new component, it is more accurate
        #  to say that face names are not propagated into a Difference component
        #  from the precursors of the difference).'''

        # Strategy 2: fusion's entityToken
        ''' in order to make use of entityToken, we will have to do our
        operation within the fusion model, rather than in the la-la land of
        tempory brep bodies '''
        boxOccurrence         = box.create_occurrence()
        boxOccurrence.component.name = 'box'
        boxBody               = boxOccurrence.bRepBodies.item(0)
        holeToolOccurrence    = holeTool.create_occurrence()
        holeToolBody          = holeToolOccurrence.bRepBodies.item(0)
        # highlight([holeToolBody,boxBody])
        initialEntityTokens = {
            'boxBodyFaces'        : [face.entityToken for face in boxBody.faces],
            'boxBodyEdges'        : [edge.entityToken for edge in boxBody.edges],
            'boxBody'             :                          boxBody.entityToken,
            'holeToolBody'        :                     holeToolBody.entityToken,
            'boxComponent'        :          boxOccurrence.component.entityToken,
            'boxOccurrence'       :                    boxOccurrence.entityToken,
            'holeToolComponent'   :     holeToolOccurrence.component.entityToken,
            'holeToolOccurrence'  :               holeToolOccurrence.entityToken,
        }

        initialEdges = list(boxBody.edges)
        

        # toolBodies=adsk.core.ObjectCollection.create()
        # toolBodies.add(holeToolBody)
        global rootComponent
        global design
        

        combineFeatureInput = rootComponent().features.combineFeatures.createInput(targetBody=boxBody, toolBodies=fscad._collection_of((holeToolBody,)))
        combineFeatureInput.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        combineFeature = rootComponent().features.combineFeatures.add(combineFeatureInput)
        # assert combineFeature is not None
        # boxBody = design().findEntityByToken(initialEntityTokens['boxBody'])[0]
        # the above does not seem to be necessary; the boxBody survives the opreration with identity (in the memory address sense) preserved.

        # highlight(boxBody)

        finalEntityTokens = {
                'boxBodyFaces'        :                            [face.entityToken for face in boxBody.faces]      ,
                'boxBodyEdges'        :                            [edge.entityToken for edge in boxBody.edges]      ,
                'boxBody'             :                          boxBody.entityToken                                 ,
                'boxComponent'        :          boxOccurrence.component.entityToken                                 ,
                'boxOccurrence'       :                    boxOccurrence.entityToken                                 ,
                # 'holeToolBody'        :                     holeToolBody.entityToken                                 ,
                'holeToolComponent'   :     holeToolOccurrence.component.entityToken                                 ,
                'holeToolOccurrence'  :               holeToolOccurrence.entityToken                                 ,
            }
        # print('design().findEntityByToken(combineFeature.entityToken): ')
        # print("\n".join(map(renderEntityToken,
        # design().findEntityByToken(combineFeature.entityToken)
        #             )
        #         )
        #     )
        # of course: in a design that has design().designType ==
        # adsk.fusion.DesignTypes.DirectDesignType , the result of doing
        # CombineFeatures::add() is null, even though "Adding" the feature did
        # have an effect on the document.

        edgesDescendedFromInitialEdges = [
            entity 
            for initialEntityToken in initialEntityTokens['boxBodyEdges']
            for entity in design().findEntityByToken(initialEntityToken)
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
            for initialEntityToken in initialEntityTokens['boxBodyFaces']
            for entity in design().findEntityByToken(initialEntityToken)
        ]

        edgesUsedByFacesDescendedFromIntialFaces = [
            edge 
            for face in facesDescendedFromInitialFaces
            for edge in face.edges
        ]

        finalEdges = list(boxBody.edges)


        # equivalently (and more computationally efficient, but perhaps harder to read):
        # initiallyExistingEdges = list(
        #     itertools.chain.from_iterable(
        #         map(
        #             design().findEntityByToken,
        #             initialEntityTokens['boxBodyEdges']
        #         )
        #     )
        # )


        print('edgesDescendedFromInitialEdges: ' + str(edgesDescendedFromInitialEdges))
        print('len(edgesDescendedFromInitialEdges): ' + str(len(edgesDescendedFromInitialEdges)))
        print("len(initialEntityTokens['boxBodyEdges']): " + str( len(initialEntityTokens['boxBodyEdges']) )    )

        # initialEdgeIds = set(map(id, initialEdges))
        # finalEdgeIds = set(map(id, finalEdges))

        # print("initialOnlyIds:" + str(initialEdgeIds.difference(finalEdgeIds)))
        # print("finalOnlyIds:" + str(finalEdgeIds.difference(initialEdgeIds)))
        # print("commonIds:" + str(finalEdgeIds.intersection(initialEdgeIds)))
        # # There are no commonIds (a python id being, in our case, the same as the memory address of the object)
        # # even though there are, intuitively, edges that have survived the operation.

        # newEdges = set(boxBody.edges) - set(edgesDescendedFromInitialEdges)  #TypeError: unhashable type: 'BRepEdge'
        # newEdges = [
        #     edge 
        #     for edge in boxBody.edges
        #     if (
        #         edge not in edgesDescendedFromInitialEdges
        #     )
        # ]

        # edgesOfInterest = [
        #     edge
        #     for edge in newEdges
        #     if edge in edgesUsedByFacesDescendedFromIntialFaces
        # ]

        edgesOfInterest = [
            edge
            for edge in boxBody.edges
            if (
                edge in edgesUsedByFacesDescendedFromIntialFaces
                and edge not in edgesDescendedFromInitialEdges
            )
        ]

        # highlight(edgesOfInterest,_fallbackComponentToReceiveTheCustomGraphics= rootComponent())
        highlight(edgesOfInterest)
        print('len(edgesOfInterest): ' + str(len(edgesOfInterest)))


        chamferFeatureInput = boxOccurrence.component.features.chamferFeatures.createInput(edges= fscad._collection_of(edgesOfInterest), isTangentChain=False)
        assert chamferFeatureInput is not None
        
        chamferFeatureInput.setToEqualDistance(adsk.core.ValueInput.createByReal(0.08))
        chamferFeature = boxOccurrence.component.features.chamferFeatures.add(chamferFeatureInput)

        assert chamferFeature is not None
        # It's interesting that the combineFeatures.add() method, above, returns None (presumably it would return a 
        # combine feature if we had design().designType = adsk.fusion.DesignTypes.ParametricDesignType rather than DirectDesignType),
        # but that chamferFeatures.add() returns a real chamferFeature.

        print("design().designType: " + str(design().designType))

        
        # edgesOfInterest = [
        #     edge in boxBody.edges
        #     if (
        #         # the edge is "the same" as one of the originally-present edges.design().findEntityByToken()
        # ]


        # edgesOfInterest : list[adsk.fusion.BRepEdge] = list(
        #     map(
        #         lambda x: design().findEntityByToken(x)[0],

        #         # we are looking for newly created edges that are used in one fo the original face's coedges.

        #     )
        # )



        if False : 
            finalCorrespondingFaceEntityTokens = [
                design().findEntityByToken(initialEntityToken)[0].entityToken
                for initialEntityToken in initialEntityTokens['boxBodyFaces'] 
            ]

            finalCorrespondingEdgeEntityTokens = [
                design().findEntityByToken(initialEntityToken)[0].entityToken
                for initialEntityToken in initialEntityTokens['boxBodyEdges'] 
            ]

           
            # intialFaceReport = ('initialFaceEntityTokens: ' + "\n" + "\n".join( map(renderEntityToken, initialFaceEntityTokens) ))

            # finalFaceReport = ('finalFaceEntityTokens: ' + "\n" + "\n".join( 
            #             (
            #                 entityToken
            #                 for entityToken in finalFaceEntityTokens 
            #             ) 
            #         )
            #     )

            # finalCorrespondingFaceReport = ('finalCorrespondingEntityTokens: ' + "\n" + "\n".join( 
            #             (
            #                 entityToken
            #                 for entityToken in finalCorrespondingFaceEntityTokens 
            #             ) 
            #         )
            #     )

            # pathlib.Path(__file__).parent.joinpath('intialFaceReport.txt').write_text(intialFaceReport)
            # pathlib.Path(__file__).parent.joinpath('finalCorrespondingFaceReport.txt').write_text(finalCorrespondingFaceReport)
            # pathlib.Path(__file__).parent.joinpath('finalFaceReport.txt').write_text(finalFaceReport)

            pathlib.Path(__file__).parent.joinpath('entityTokenReport.txt').write_text(
                    "\n\n".join((
                        "rootComponent().entityToken: "                + renderEntityToken(rootComponent().entityToken),
                        
                        "initialEntityTokens['boxBodyFaces'] : "       + "\n" + "\n".join( map(renderEntityToken, initialEntityTokens['boxBodyFaces']   ) ),
                        "finalCorrespondingFaceEntityTokens: "         + "\n" + "\n".join( map(renderEntityToken, finalCorrespondingFaceEntityTokens    ) ) ,
                        "finalEntityTokens['boxBodyFaces'] : "         + "\n" + "\n".join( map(renderEntityToken, finalEntityTokens['boxBodyFaces']     ) ),
                        
                        "initialEntityTokens['boxBodyEdges']: "        + "\n" + "\n".join( map(renderEntityToken, initialEntityTokens['boxBodyEdges']   ) ),
                        "finalCorrespondingEdgeEntityTokens: "         + "\n" + "\n".join( map(renderEntityToken, finalCorrespondingEdgeEntityTokens    ) ),
                        "finalEntityTokens['boxBodyEdges']: "          + "\n" + "\n".join( map(renderEntityToken, finalEntityTokens['boxBodyEdges']     ) ),

                        "initialEntityTokens [ 'boxComponent'       ]: "  + renderEntityToken(initialEntityTokens [ 'boxComponent'       ]),
                        "finalEntityTokens   [ 'boxComponent'       ]: "  + renderEntityToken(finalEntityTokens   [ 'boxComponent'       ]),
                        "initialEntityTokens [ 'boxOccurrence'      ]: "  + renderEntityToken(initialEntityTokens [ 'boxOccurrence'      ]),
                        "finalEntityTokens   [ 'boxOccurrence'      ]: "  + renderEntityToken(finalEntityTokens   [ 'boxOccurrence'      ]),
                        "initialEntityTokens [ 'boxBody'            ]: "  + renderEntityToken(initialEntityTokens [ 'boxBody'            ]),
                        "finalEntityTokens   [ 'boxBody'            ]: "  + renderEntityToken(finalEntityTokens   [ 'boxBody'            ]),

                        "initialEntityTokens [ 'holeToolComponent'  ]: "  + renderEntityToken(initialEntityTokens [ 'holeToolComponent'  ]),
                        "finalEntityTokens   [ 'holeToolComponent'  ]: "  + renderEntityToken(finalEntityTokens   [ 'holeToolComponent'  ]),
                        "initialEntityTokens [ 'holeToolOccurrence' ]: "  + renderEntityToken(initialEntityTokens [ 'holeToolOccurrence' ]),
                        "finalEntityTokens   [ 'holeToolOccurrence' ]: "  + renderEntityToken(finalEntityTokens   [ 'holeToolOccurrence' ]),
                        "initialEntityTokens [ 'holeToolBody'       ]: "  + renderEntityToken(initialEntityTokens [ 'holeToolBody'       ]),
                        # "finalEntityTokens   [ 'holeToolBody'       ]: "  + renderEntityToken(finalEntityTokens   [ 'holeToolBody'       ]),
        
                    ))
                )

            f = open(pathlib.Path(__file__).parent.joinpath('entityTokensAcrossRuns.txt'), 'a')            
            f.write(renderEntityToken(initialEntityTokens['boxBodyFaces'][0]) + "\n")
            f.close()

            # print('finalFaceEntityTokens: ' + "\n\t" + "\n\t".join(finalFaceEntityTokens))

            # print('initialEdgeEntityTokens: ' + "\n\t" + "\n\t".join(initialEdgeEntityTokens))
            
            # print('finalEdgeEntityTokens: ' + "\n\t" + "\n\t".join(finalEdgeEntityTokens))

            # entityTokenPieces = (
            #     for entityToken in (initialFaceEntityTokens + )
            # )

        # design().findEntityByToken()


        '''
             highlight(
                 edgesToHighlight,
                 _fallbackComponentToReceiveTheCustomGraphics=mainOccurrence.component.parentDesign.rootComponent
                 )

         trying to highlight the edges after we have run
         fscad.Component::create_occurrence runs counter to the fscad philosophy
         that the true assembly structure exists only within the fscad-native
         'Component' object, and that the fusion-native object is merely
         ephemeral.

         The correct way to do highlighitin in keeping with the fscad philosophy
         would be to have fscad be aware of the hihglighting, and have the
         creation of the customgraphicsentities occur as part of the fscad
         create_occurrence routine. Alternatively, we could imagine augmenting
         the fscad component object with the ability to remember the various
         fusion components and occurrences that it had created, so that,, even
         after calling fscad.component::create_occurrence(), we could make
         subsequent changes to the already-crerated fusion-native objects by
         calling other methods on the original fscad.component.  As it is,
         fscad.component::create_occurrence() causes zero modification of the
         fscad.componetn object.  The fscad.component has no knowledge of, or
         connection with, the fusion-native objects that it created during a
         porevious running of its create_occurrence() method.  
         Thus, for our goal of doing the highlighting at this point starting
         with the fscad-native edge object, we are in the dark about where
         within the fusion component hierarchy to put the graphics entities that
         constitute the highlight. actually, we are not entirely in the dark --
         we do have the Occurrence object that create_occurrence() produced. '''

        # highlight( entitiesToHighlight,  _fallbackComponentToReceiveTheCustomGraphics=mainOccurrence.component)
          
    ''' fscad requires that designType be DirectDesignType, not
     ParametricDesignType.  If you attempt to run fscad's create_occurrence()
     function when designType is ParametricDesignType, the result will be the
     error: "RuntimeError: 3 : A valid targetBaseFeature is required" .  
     
         adsk.fusion.Design.cast(app().activeProduct).designType = adsk.fusion.DesignTypes.DirectDesignType
     '''

    def design2_deprecated1():

        # x = bit_holder.castToNDArray(adsk.core.Point3D.create(2,3,4))
        # y = bit_holder.castTo3dArray(adsk.core.Point3D.create(2,3,4))
        # z = bit_holder.castTo3dArray(adsk.core.Point2D.create(2,3))
        # z=bit_holder.castTo3dArray((1*bit_holder.millimeter, 3*bit_holder.millimeter))
        # print('x: ' + str(x))
        # print('y: ' + str(y))
        # print('z: ' + str(z))
        # return

        # bit_holder.BitHolderSegment().create_occurrence()

        # bit_holder.TextRow(
        #         fontName="Times New Roman",
        #         text="Abc"
        #     ).create_occurrence()

        mm = bit_holder.millimeter
        g = bit_holder.Galley(
                fontName=("Times New Roman","Arial"),
                # text="  sadf                                       ",
                text="A\\floodWithInk",
                width = 40*mm,
                height = 60*mm,
                rowSpacing = 1.5,
                rowHeight = (5*mm,2*mm) ,
                horizontalAlignment = bit_holder.HorizontalAlignment.LEFT,
                verticalAlignment = bit_holder.VerticalAlignment.CENTER,
                clipping=True,
                leftMargin=5*mm,
                rightMargin=5*mm,
                topMargin=5*mm,
                bottomMargin=5*mm
            ).translate(2.9,3.9)
        o=g.create_occurrence()
        o.isLightBulbOn = False
        highlight(g)
        # highlight(g.extentBox.translate(tz=-2))
        # highlight(adsk.core.Point3D.create(0.5,0.3,0))
        
        # p = adsk.core.Point3D.create(0, 0, 0); p.transformBy(g.world_transform()); highlight(p)
        highlight(g.world_transform().getAsCoordinateSystem()[0])

        g.extentBox.translate(tz=-2).create_occurrence()
        g.marginBox.translate(tz=-1).create_occurrence()

        appearances = o.component.parentDesign.appearances
        appearance : adsk.core.Appearance = appearances.addByCopy(appearanceToCopy=appearances[0], name='george-'+str(uuid.uuid4()))
        # appearanceProperty : adsk.core.Property
        # print(
        #     tuple(
        #         (appearanceProperty.id, appearanceProperty.name, appearanceProperty.objectType, 
        #             (
        #                 tuple(
        #                     value.getColor()
        #                     for value in appearanceProperty.values
        #                 )
        #                 if isinstance(appearanceProperty, adsk.core.ColorProperty) and appearanceProperty.values
        #                 else ''
        #             )
        #         )
        #         for appearanceProperty in 
        #         appearance.appearanceProperties 
        #         # if isinstance(appearanceProperty, adsk.core.ColorProperty) and appearanceProperty.values
        #     )
        # )

        # for appearanceProperty in appearance.appearanceProperties :
        #     if isinstance(appearanceProperty, adsk.core.ColorProperty):
        #         for i in range(len(appearanceProperty.values)):
        #             # appearanceProperty.values[i] =  adsk.core.Color.create(red=0, green=140, blue=0, opacity=100)
        #             appearanceProperty.values[i].setColor(red=0, green=140, blue=0, opacity=100)
        #         # appearanceProperty.values = [
        #         #     adsk.core.Color.create(red=255, green=0, blue=0, opacity=100),
        #         #     adsk.core.Color.create(red=0, green=255, blue=0, opacity=102)
        #         # ]
                
        #         appearanceProperty.values = list(
        #             adsk.core.Color.create(red=0, green=140, blue=0, opacity=100)
        #             for color in appearanceProperty.values
        #         )


        #         print(
        #             tuple(
        #                 value.getColor()
        #                 for value in appearanceProperty.values
        #             )
        #         )

        # bit_holder.rectByCorners(
        #     corner1=(5*mm,10*mm),
        #     corner2=(17*mm,30*mm)
        # ).create_occurrence()

        # highlight(rectByCorners())

        # r = bit_holder.rectByCorners(
        #     corner1=(1*bit_holder.millimeter, 6*bit_holder.millimeter),
        #     corner2=(5*bit_holder.millimeter, 3*bit_holder.millimeter)
        # )
        # # r.create_occurrence()
        # print('type(r): ' + str(type(r)))

        # highlight(r.edges)

        # fscadComponent = bitHolderSegment.build()
        # fscadComponent.create_occurrence()

        a : adsk.core.Point2D = adsk.core.Point2D.create(11,22)
        b : adsk.core.Point3D = adsk.core.Point3D.create(11,22,33)
        aa : adsk.core.Point3D = adsk.core.Point3D.cast(a)
        bb : adsk.core.Point2D = adsk.core.Point2D.cast(b)

        print('a.asArray(): ' + str(a.asArray()))
        print('b.asArray(): ' + str(b.asArray()))
        
        print('aa is None: ' + str(aa is None))
        print('aa and aa.asArray(): ' + str(aa and aa.asArray()))
        print('bb is None: ' + str(bb is None))
        print('bb and bb.asArray(): ' + str(bb and bb.asArray()))


        p2 : adsk.core.Point2D = adsk.core.Point2D.create(11,22)
        p3 : adsk.core.Point3D = adsk.core.Point3D.create(11,22,33)
        v2 : adsk.core.Vector2D = adsk.core.Vector2D.create(11,22)
        v3 : adsk.core.Vector3D = adsk.core.Vector3D.create(11,22,33)

        # x=adsk.core.Point3D = adsk.core.Point3D.cast(tuple(11,22,33))
        # x=adsk.core.Point3D = adsk.core.Point3D.cast(v3) running either of the
        # above two cast statement once causes the python interpreter to
        # subsequently not recognize adsk.core.Point3D as a type. Very weird.
        
        # print('x and x.asArray(): ' + str(x and x.asArray()))
        

    def design2():
        # v = adsk.core.Vector3D.create(0,0,0)
        # v = adsk.core.Vector3D.create(False, False, False)

        # myBitHolderSegment = bit_holder.BitHolderSegment(
        #     # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
        #     # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
        #     bit=bit_holder.Bit(
        #         labelText="\\floodWithInk"
        #         #labelText="ABC"
        #     ),
        #     minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
        #     doLabelRetentionLip=True,
        #     directionsOfEdgesThatWeWillAddALabelRetentionLipTo=(
        #         bit_holder.xHat,
        #         # bit_holder.yHat,
        #         # bit_holder.zHat,
        #     )
        # )
        
        # myBitHolderSegment.create_occurrence()


        if False:
            myBitHolder = bit_holder.BitHolder(
                segments = [
                    bit_holder.BitHolderSegment(
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
                        bit= bit_holder.Bit(
                                labelText="\\floodWithInk"
                                #labelText="ABC"
                            ),
                        minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
                        doLabelRetentionLip=True,
                        directionsOfEdgesThatWeWillAddALabelRetentionLipTo=(
                            bit_holder.xHat,
                            # bit_holder.yHat,
                            # bit_holder.zHat,
                        )
                    )
                    for i in range(6)
                ] + [
                    bit_holder.BitHolderSegment(
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
                        bit= bit_holder.Socket(
                                driveSize   = 3/8 * bit_holder.inch,
                                length      = 25.96 * bit_holder.millimeter,
                                nominalUnit = 1*bit_holder.inch,
                                nominalSize = 3/8 * bit_holder.inch,
                                outerDiameter = 17.18 * bit_holder.millimeter
                            ),
                        labelFontHeight=(4.75 * bit_holder.millimeter, 3.2 * bit_holder.millimeter),
                        minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
                        doLabelRetentionLip=False
                    )
                ]
            )
            
        # myBitHolder = bit_holder.getCannedBitHolders()['bondhus_hex_drivers_holder']
        # myBitHolder.create_occurrence()

        # startTime = time.time()
        # bit_holder.getCannedBitHolders()
        # endTime = time.time()
        # print("duration of first bit_holder.getCannedBitHolders(): %f" % (endTime-startTime))


        # startTime = time.time()
        # bit_holder.getCannedBitHolders()
        # endTime = time.time()
        # print("duration of second bit_holder.getCannedBitHolders(): %f" % (endTime-startTime))

        startTime = time.time()
        # bitHolderArray = bit_holder.makeBitHolderArray(*list(bit_holder.getCannedBitHolders().values())[0:1]*3)
        
        myBitHolder = list(bit_holder.getCannedBitHolders().values())[0]
        initialSegments = myBitHolder.segments
        x = initialSegments[0]
        # y = x.copy()

        # myBitHolder.segments = (initialSegments[0].copy(), initialSegments[0].copy(), initialSegments[1])
        myBitHolder.segments = (initialSegments[i] for i in (0,1,1,1,0))
        bitHolderArray = bit_holder.makeBitHolderArray(*[myBitHolder]*3)
        endTime = time.time()
        print("duration of makeBitHolderArray: %f" % (endTime-startTime))

        startTime = time.time()
        bitHolderArray.create_occurrence()
        endTime = time.time()
        print("duration of bitHolderArray.create_occurrence(): %f" % (endTime-startTime))




    #monkeypatching traceback with the vscode-compatible link formatting

    initialTracebackStackSummaryFormatMethod = formatStackSummary
    traceback.StackSummary.format = formatStackSummary

    fscad.run_design(design_func=design2, message_box_on_error=False)
    traceback.StackSummary.format = initialTracebackStackSummaryFormatMethod
    # run_design(design_func=design2, message_box_on_error=False)
    # print(traceback.format_tb(sys.last_traceback))

    print(f"finished running {__file__}")
    #     ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    # prevent this module from being terminated when the script returns
    #     adsk.autoTerminate(False)

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass


# #this is a near-copy of fscad.run_design() with a slightly different exception handler to
# # format traceback reports in such a way that the file names and line numbers in the traceback report
# # will be interpreted by vscode as links to specific lines in the file.
# def run_design(design_func, message_box_on_error=True, print_runtime=True, document_name=None,
#                design_args=None, design_kwargs=None):
#     """Utility method to handle the common setup tasks for a script

#     This can be used in a script like this::

#         from fscad import *
#         def run(_):
#             run_design(_design, message_box_on_error=False, document_name=__name__)

#     Args:
#         design_func: The function that actually creates the design
#         message_box_on_error: Set true to pop up a dialog with a stack trace if an error occurs
#         print_runtime: If true, print the amount of time the design took to run
#         document_name: The name of the document to create. If a document of the given name already exists, it will
#             be forcibly closed and recreated.
#         design_args: If provided, passed as unpacked position arguments to design_func
#         design_kwargs: If provided, passed as unpacked named arguments to design_func
#     """
#     # noinspection PyBroadException
#     try:
#         start = time.time()
#         if not document_name:
#             frame = inspect.stack()[1]
#             module = inspect.getmodule(frame[0])
#             filename = module.__file__
#             document_name = pathlib.Path(filename).stem
#         fscad.setup_document(document_name)
#         design_func(*(design_args or ()), **(design_kwargs or {}))
#         end = time.time()
#         if print_runtime:
#             print("Run time: %f" % (end-start))
#     except Exception:
#         print(traceback.format_exc())
#         etype, evalue, tb = sys.exc_info()
#         stackSummary = traceback.extract_tb(tb)
#         # print("\n".join(traceback.format_list(stackSummary)))
#         # print("---")
#         print("".join(formatStackSummary(stackSummary)))
#         if message_box_on_error:
#             ui().messageBox('Failed:\n{}'.format(traceback.format_exc()))

#copied, with modification, from the python library function traceback.StackSummary::format()
# we are tweaking the format of the file name and line number information to conform with
# the relatively strict format (filename followed b y a colon followed by the line number) that
# vscode must have in the debug console output in order to automatically create a link
# to zap to the specified line number in the specified file.
def formatStackSummary(stackSummary : traceback.StackSummary) -> Sequence[str]:
    """Format the stack ready for printing.

    Returns a list of strings ready for printing.  Each string in the
    resulting list corresponds to a single frame from the stack.
    Each string ends in a newline; the strings may contain internal
    newlines as well, for those items with source text lines.

    For long sequences of the same frame and line, the first few
    repetitions are shown, followed by a summary line stating the exact
    number of further repetitions.
    """
    result = []
    last_file = None
    last_line = None
    last_name = None
    count = 0
    for frame in stackSummary:
        if (last_file is None or last_file != frame.filename or
            last_line is None or last_line != frame.lineno or
            last_name is None or last_name != frame.name):
            if count > traceback._RECURSIVE_CUTOFF:
                count -= traceback._RECURSIVE_CUTOFF
                result.append(
                    f'  [Previous line repeated {count} more '
                    f'time{"s" if count > 1 else ""}]\n'
                )
            last_file = frame.filename
            last_line = frame.lineno
            last_name = frame.name
            count = 0
        count += 1
        if count > traceback._RECURSIVE_CUTOFF:
            continue
        row = []
        # row.append('  File "{}", line {}, in {}\n'.format(
        row.append('  File "{}:{}" in {}\n'.format(
            frame.filename, frame.lineno, frame.name))
        if frame.line:
            row.append('    {}\n'.format(frame.line.strip()))
        if frame.locals:
            for name, value in sorted(frame.locals.items()):
                row.append('    {name} = {value}\n'.format(name=name, value=value))
        result.append(''.join(row))
    if count > traceback._RECURSIVE_CUTOFF:
        count -= traceback._RECURSIVE_CUTOFF
        result.append(
            f'  [Previous line repeated {count} more '
            f'time{"s" if count > 1 else ""}]\n'
        )
    return result

#monkeypatching traceback:
traceback.StackSummary.format = formatStackSummary