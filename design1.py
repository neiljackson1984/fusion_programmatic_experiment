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

    def my_design():
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

    fscad.run_design(design_func=my_design, message_box_on_error=False)

    print("finished creating new bolts")
    #     ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    # prevent this module from being terminated when the script returns
    #     adsk.autoTerminate(False)

FusionBRepEntity = (
    Union[
        adsk.fusion.BRepBody,
        adsk.fusion.BRepFace,
        adsk.fusion.BRepLoop,
        adsk.fusion.BRepEdge,
        adsk.fusion.BRepVertex,
        # might consider including all adsk.fusion.BRep* classes, because pretty much all of them can be logically converted into a BRepBody
    ])

def makeFusionBRepBodyFromFusionBRepEntity(fusionBRepEntity : FusionBRepEntity) -> Optional[adsk.fusion.BRepBody]:
    temporaryBRepManager : adsk.fusion.TemporaryBRepManager = adsk.fusion.TemporaryBRepManager.get()
    # we end up not having to reinvent the wheel as much as I first thought because this functionality is already built into fusion
    # # in the form of the temporaryBRepManager.copy() function,
    # at least for the case of BRepFace, BRepLoop, and BRepEdge, according to the codumentation
    # (although I would think that maybe BRepVertex might work exactly the same way?):
    # temporaryBRepManager.copy() takes any of the following types of object as argument:
    # adsk.fusion.BRepBody, adsk.fusion.BRepFace, adsk.fusion.BRepLoop, adsk.fusion.BRepEdge'
    # what happens if we try to give it a BRepVertex or a BRepCoedge?
    
    if   isinstance(fusionBRepEntity, (adsk.fusion.BRepBody, adsk.fusion.BRepFace, adsk.fusion.BRepLoop, adsk.fusion.BRepEdge)):
        newBRepBody = temporaryBRepManager.copy(fusionBRepEntity)
    elif isinstance(fusionBRepEntity, adsk.fusion.Vertex):
        newBRepBody = temporaryBRepManager.copy(fusionBRepEntity)
        #I suspect that the above will not work.
    else:
        #this is a type error
        return None

 
    #region DEPRECATED_HARD_WAY
    # elif isinstance(fusionBRepEntity, adsk.fusion.BRepFace):
    #     sourceBRepFace : adsk.fusion.BRepFace = fusionBRepEntity
        # # we have to construct a new brepBody that consists of only this face
        # # one strategy for constructing such a body might be to make a copy of the body to which this face belongs,
        # # then delete all the other faces.
        # # another strategy, which I am pursuing here, is to construct the new body from scratch using the underlying 
        # # 2dcurve and surface geometry that defines the face.
        
        # #things that we might need to pull out of bRepFace (and stick into the appropriate slots in brepBodyDefinition) in order to construct the new brepBody:
        # #  bRepFace.geometry
        # #  bRepFace.loops
        # #  bRepFace.edges 
        # #  bRepFace.vertices 

        
        # bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()
        # brepLumpDefinition  = bRepBodyDefinition.lumpDefinitions.add()
        # brepShellDefinition = brepLumpDefinition.shellDefinitions.add()
        # brepFaceDefinition  = brepShellDefinition.faceDefinitions.add(surfaceGeometry=sourceBRepFace.geometry, isParamReversed=sourceBRepFace.isParamReversed)
        # # we must construct a set of edge definitions, one for each edge in sourceBRepFace.
        # # I think it might be important not to construct a fresh edge definition for each coedge because we could have the case (I think)
        # # where multiple coedges refer to the same edge, and we want to preserve that structure in the newly-created body.
        # # same goes for not constructing fresh vertexDefinitions for each edge because we could (and almost certainly will) have the case where multiple edges refer to the same vertex.
        # # sourceVerticesToDestinationVertexDefinitions : dict[adsk.fusion.BRepVertex, adsk.fusion.BRepVertexDefinition] = {
        # #     sourceVertex: bRepBodyDefinition.createVertexDefinition(sourceVertex.geometry)
        # #     for sourceVertex in sourceBRepFace.vertices
        # # }
        # # oops, BRepVertex is not a hashable type, apparently, (why the hell not?) and therefore cannot be used as a dict key
        # # fusion's tempId's are the obvious intended way to do what I want to do
        # sourceVertexTempIdsToDestinationVertexDefinitions : dict[int, adsk.fusion.BRepVertexDefinition] = {
        #     sourceVertex.tempId: bRepBodyDefinition.createVertexDefinition(sourceVertex.geometry)
        #     for sourceVertex in sourceBRepFace.vertices
        # }
        

        # # sourceEdgesToDestinationEdgeDefinitions : dict[adsk.fusion.BRepEdge, adsk.fusion.BRepEdgeDefinition] = {
        # #     sourceEdge: bRepBodyDefinition.createEdgeDefinitionByCurve(
        # #         startVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.startVertex.tempId],
        # #         endVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.endVertex.tempId],
        # #         modelSpaceCurve=sourceEdge.geometry
        # #     )
        # #     for sourceEdge in sourceBRepFace.edges
        # # }
        # # oops, BRepEdge is not a hashable type, apparently, (why the hell not?) and therefore cannot be used as a dict key
        # # fusion's tempId's are the obvious intended way to do what I want to do
        # sourceEdgeTempIdsToDestinationEdgeDefinitions : dict[int, adsk.fusion.BRepEdgeDefinition] = {
        #     sourceEdge.tempId: bRepBodyDefinition.createEdgeDefinitionByCurve(
        #         startVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.startVertex.tempId],
        #         endVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.endVertex.tempId],
        #         modelSpaceCurve=sourceEdge.geometry
        #     )
        #     for sourceEdge in sourceBRepFace.edges
        # }


        # for bRepLoop in sourceBRepFace.loops:
        #     bRepLoop = adsk.fusion.BRepLoop.cast(bRepLoop)
        #     bRepLoopDefinition = brepFaceDefinition.loopDefinitions.add()
        #     # bRepLoop is the 'source' object from which we are copying information.
        #     # bRepLoopDefinition is the new object that we are creating, and copying the information into.
        #     for bRepCoEdge in bRepLoop.coEdges:
        #         #source: 
        #         bRepCoEdge = adsk.fusion.BRepCoEdge.cast(bRepCoEdge)
        #         #destination:
        #         bRepCoEdgeDefinition = bRepLoopDefinition.bRepCoEdgeDefinitions.add(
        #             edgeDefinition= sourceEdgeTempIdsToDestinationEdgeDefinitions[bRepCoEdge.edge.tempId],
        #             isOpposedToEdge=bRepCoEdge.isOpposedToEdge 
        #         )
        
        # newBRepBody = bRepBodyDefinition.createBody()

        # if not newBRepBody:
        #     print(
        #         "While attempting to convert adsk.fusion.BRepFace into a new adsk.fusion.BRepBody, we were unable to create a BRepBody. " 
        #         +  'bRepBodyDefinition.outcomeInfo: ' + "\n" + "\n".join(bRepBodyDefinition.outcomeInfo)
        #     )
        #     return
    #endregion

    return newBRepBody


HighlightableThing = (
        Union[
            adsk.fusion.BRepEdge, 
            adsk.fusion.BRepFace, 
            adsk.core.Curve3D, 
            adsk.fusion.BRepBody, 
            adsk.fusion.Occurrence, 
            fscad.BRepEntity
        ])

def highlight(
    x: Union[HighlightableThing, Sequence[HighlightableThing]],
    _customGraphicsGroupToReceiveTheCustomGraphics : Optional[adsk.fusion.CustomGraphicsGroup] = None,
    _fallbackComponentToReceiveTheCustomGraphics : Optional[adsk.fusion.Component] = None
    ):

    """ The highlight will consist of custom graphics entities.  Custom graphics
    objects must exist as a member of a custom graphics group, and
    a custom graphics group is contained either in another custom graphics group or
    in a component's CustomGraphicsGroups collection (i.e. a custom graphics entity
    is contained within a custom graphics group which is contained (possibly nested
    within other groups) within a component. We (or, more typically, the highlight
    function calling itself), can explicitly specify the particular custom graphics
    group in which to place the newly-created graphics entities, or can explicitly
    specify the component in which to place the newly-created graphics entities. If
    you specify _customGraphicsGroupToReceiveTheCustomGraphics, then the
    _componentToReceiveTheCustomGraphics argument is ignored (Even if you specify
    it).

    Ideally, the correct component could always be resolved by inspecting the
    highlightable thing.  However, in the case where the highlightable thing is a
    temporary brep body or a Curve3D or some other bit of "pure" geometry, the
    highlightable thing does not belong to any component, so we must specify the
    component as a separate argument. We will place the highlight in the component
    specified by _fallbackComponentToReceiveTheCustomGraphics only if we cannot
    figure out the component manually. in other words, we will look at the
    following pieces of information, in this order, to decide in which graphics
    group to place the customGraphics entities:
    1) _customGraphicsGroupToReceiveTheCustomGraphics argument, if specified,
    2) try to determine the correct component by inspecting the highlightable
        thing,
    3) Use the _fallbackComponentToReceiveTheCustomGraphics In cases 2 and 3, we
        will arrive at a component in which to place the custom grpahics, and will
        then use an automatic process to figure out which graphics group to place
        the custom graphics (creating the graphics group if it does not already
        exist).
     """
    # if xIsASequenceOfHighlightableThing:
    if isinstance(x, Sequence):
        for y in x: highlight(y, _customGraphicsGroupToReceiveTheCustomGraphics=_customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)
        return

    #at this point, it is safe to assume that x is a HighlightableThing
    highlightableThing : HighlightableThing = x

    preferredWeight = 3
    preferredColor  = adsk.core.Color.create(red=255, green=0, blue=0, opacity=255)
    preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)

    if   isinstance(highlightableThing, adsk.fusion.Occurrence  ):
        occurrence : adsk.fusion.Occurrence = highlightableThing
        #not yet supported
        print( "highlighting a adsk.fusion.Occurrence is not yet supported." )
        return  
    elif isinstance(highlightableThing, adsk.fusion.BRepBody    ):
        bRepBody : adsk.fusion.BRepBody = highlightableThing
        if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        else:
            #figure out which component we want to add custom graphics to
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = (
                (bRepBody.assemblyContext and bRepBody.assemblyContext.sourceComponent)
                or bRepBody.parentComponent
                or _fallbackComponentToReceiveTheCustomGraphics
            )
            
            if componentToReceiveTheCustomGraphics is None:
                #this is an error. we were unable to figure out a component in which to place the custom graphics, so we cannot proceed.
                print("while attempting to highlight a adsk.fusion.BRepBody, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
                return
            
            # retrieve, or create, the customGraphicsGroup within componentToReceiveCustomGraphics.customGraphicsGroups (possibly a sub... group) to which we will add the customGraphicsEntity
            # should we add a new customGraphicsGroup for each edge to be highlighted? probably not.  However, for simplicity of the code, I will, at the moment, adopt this strategy.
            # should we simply use the first customGraphicsGroup in componentToReceiveCustomGraphics.customGraphicsGroups (creating it if it does not exist)
            # should we have one special customGraphicsGroup in each component that is dedicated to containing our custom graphics highlighting entities?  Something along these lines is probably the correct answer, but 
            # I will defer implementing such a system for now (mainly because it would be a bit of work to figure out how to keep track of and retrieve/create the special custom graphics group.
            # I do not understand how graphics groups are meant to be used.  Presumably, the intent is to set up some sort of cascading inheritance structure for graphical properties, so 
            # that properties assigned to a group will become the defaults for all then members of the group.
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()
        customGraphicsBRepBody : Optional[adsk.fusion.CustomGraphicsBRepBody] = customGraphicsGroupToReceiveTheCustomGraphics.addBRepBody(bRepBody) 
        
        #mainly for debugging, let's give bodies a different color from curves:
        preferredColor  = adsk.core.Color.create(red=255, green=130, blue=255, opacity=255)
        preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)

        customGraphicsBRepBody.color=preferredCustomGraphicsColorEffect
    elif isinstance(highlightableThing, fscad.BRepEntity        ):
        bRepEntity : fscad.BRepEntity = highlightableThing
        # pylance seems to be smart enough not to need the above line for type inference, but I want it for my own sanity.
        highlight(bRepEntity.brep, 
            _customGraphicsGroupToReceiveTheCustomGraphics=_customGraphicsGroupToReceiveTheCustomGraphics, 
            _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics
        )
    elif isinstance(highlightableThing, adsk.fusion.BRepEdge    ):
        bRepEdge : adsk.fusion.BRepEdge = highlightableThing
        # is there any benefit to doing adsk.fusion.BRepEdge.cast()?
        # entity = adsk.fusion.BRepEdge.cast(entity)
        # pylance seems to be smart enough not to need the above line for type inference.  I am not sure if there would be any other advantage to doing a adsk.fusion.BRepEdge.cast()
        if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        else:
            #figure out which component we want to add custom graphics to
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = (
                (bRepEdge.body.assemblyContext and bRepEdge.body.assemblyContext.sourceComponent)
                or bRepEdge.body.parentComponent
                or _fallbackComponentToReceiveTheCustomGraphics
            )
            
            if componentToReceiveTheCustomGraphics is None:
                #this is an error. we were unable to figure out a component in which to place the custom graphics, so we cannot proceed.
                print("while attempting to highlight a adsk.fusion.BRepEdge, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
                return
            
            # retrieve, or create, the customGraphicsGroup within componentToReceiveCustomGraphics.customGraphicsGroups (possibly a sub... group) to which we will add the customGraphicsEntity
            # should we add a new customGraphicsGroup for each edge to be highlighted? probably not.  However, for simplicity of the code, I will, at the moment, adopt this strategy.
            # should we simply use the first customGraphicsGroup in componentToReceiveCustomGraphics.customGraphicsGroups (creating it if it does not exist)
            # should we have one special customGraphicsGroup in each component that is dedicated to containing our custom graphics highlighting entities?  Something along these lines is probably the correct answer, but 
            # I will defer implementing such a system for now (mainly because it would be a bit of work to figure out how to keep track of and retrieve/create the special custom graphics group.
            # I do not understand how graphics groups are meant to be used.  Presumably, the intent is to set up some sort of cascading inheritance structure for graphical properties, so 
            # that properties assigned to a group will become the defaults for all then members of the group.
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()

        # bRepBody = makeFusionBRepBodyFromFusionBRepEntity(bRepEdge)
        # if not bRepBody:
        #     print(
        #         "While attempting to highlight a adsk.fusion.BRepEdge, we were unable to create a BRepBody to serve as a custom graphics entity.  " 
        #     )
        #     return
        # highlight(bRepBody, _customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)
        # as expected, the above does not work because of Fusion's hangups about wire bodies.

        highlight(bRepEdge.geometry, _customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)

    elif isinstance(highlightableThing, adsk.fusion.BRepFace    ):
        bRepFace : adsk.fusion.BRepFace = highlightableThing
        # come up with customGraphicsGroupToReceiveTheCustomGraphics
        if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        else:
            #figure out which component we want to add custom graphics to
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = (
                (bRepFace.body.assemblyContext and bRepFace.body.assemblyContext.sourceComponent)
                or bRepFace.body.parentComponent
                or _fallbackComponentToReceiveTheCustomGraphics
            )
            
            if componentToReceiveTheCustomGraphics is None:
                #this is an error. we were unable to figure out a component in which to place the custom graphics, so we cannot proceed.
                print("while attempting to highlight an adsk.fusion.BRepFace, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
                return
            
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()

        # highlight(bRepFace.geometry, _customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)
        bRepBody = makeFusionBRepBodyFromFusionBRepEntity(bRepFace)

        if bRepBody is None:
            print(
                "While attempting to highlight a adsk.fusion.BRepFace, we were unable to create a BRepBody to serve as a custom graphics entity.  " 
            )
            return

        highlight(bRepBody, _customGraphicsGroupToReceiveTheCustomGraphics=customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)


    elif isinstance(highlightableThing, adsk.core.Curve3D       ):
        curve3D : adsk.core.Curve3D = highlightableThing
        if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        elif _fallbackComponentToReceiveTheCustomGraphics is not None:
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = _fallbackComponentToReceiveTheCustomGraphics
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()
        else:
            print("while attempting to highlight an adsk.core.Curve3D, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
            # this is an error, we cannot figure out which component to place the custom graphics entities, so we cannot proceed.
            return
        customGraphicsCurve : Optional[adsk.fusion.CustomGraphicsCurve] = customGraphicsGroupToReceiveTheCustomGraphics.addCurve(curve3D) 
        customGraphicsCurve.weight=preferredWeight
        customGraphicsCurve.color=preferredCustomGraphicsColorEffect
    elif isinstance(highlightableThing, adsk.core.Surface       ): #NOT REALLY SUPPORTED, OR MEANINGFUL
        # it probably does not make sense to highlight a surface, because a surface is unbounded (or not explicitly bounded) geometry.
        # the below technique will fail consistently because, at the moment, I have not done anything to construct a useful set of loops for the face.
        
        surface : adsk.core.Surface = highlightableThing
        temporaryBRepManager : adsk.fusion.TemporaryBRepManager = adsk.fusion.TemporaryBRepManager.get()
        bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()
        brepLumpDefinition = bRepBodyDefinition.lumpDefinitions.add()
        brepShellDefinition = brepLumpDefinition.shellDefinitions.add()
        brepFaceDefinition = brepShellDefinition.faceDefinitions.add(surfaceGeometry=surface, isParamReversed=False)

        bRepBody = bRepBodyDefinition.createBody()

        if not bRepBody:
            print(
                "While attempting to highlight a adsk.core.Surface, we were unable to create a BRepBody to serve as a custom graphics entity.  " 
                +  'bRepBodyDefinition.outcomeInfo: ' + "\n" + "\n".join(bRepBodyDefinition.outcomeInfo)
            )
            return

        # bRepBody = temporaryBRepManager.
        if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        elif _fallbackComponentToReceiveTheCustomGraphics is not None:
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = _fallbackComponentToReceiveTheCustomGraphics
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()
        else:
            print("while attempting to highlight an adsk.core.Surface, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
            # this is an error, we cannot figure out which component to place the custom graphics entities, so we cannot proceed.
            return

        customGraphicsBRepBody : Optional[adsk.fusion.CustomGraphicsBRepBody] = customGraphicsGroupToReceiveTheCustomGraphics.addBRepBody(bRepBody) 
        customGraphicsBRepBody.color=preferredCustomGraphicsColorEffect
    else:
        print("We do not know how to highlight a " + str(type(highlightableThing)))
        return
        #this is a type error

#region DEPRECATED_HIGHLIGHTING
# def highlightEntities(entities: Sequence[HighlightableThing], 
    
#     _customGraphicsGroupToReceiveTheCustomGraphics : Optional[adsk.fusion.CustomGraphicsGroup] = None
    
#     ):
#     # how to graphically highlight an arbitrary set of edges:

  
#     doSketchBasedHighlight = False
#     doBodyBasedHighlight = False 
#     doCustomGraphicsBRepBodyBasedHighlight = False
#     doCustomGraphicsCurveBasedHighlight = True

#     preferredWeight=3
#     preferredColor = adsk.core.Color.create(red=255, green=0, blue=0, opacity=255)
#     preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)

#     # if doSketchBasedHighlight:
#     #     edgeHighlightingSketch : Optional[adsk.fusion.Sketch] = mainOccurrence.component.sketches.add(mainOccurrence.component.xYConstructionPlane)
#     #     for curve in curvesToHighlight:
#     #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(curve) # throws type error
#     #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(adsk.core.NurbsCurve3D.cast(curve)) # throws RuntimeError: 3 : Invalid argument nurbsCurve
#     #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(adsk.core.NurbsCurve3D(curve)) # throws "no constructor defined" error.
            
#     #         # convert the curve into a nurbsCurve3D object.
#     #         # the conversion method varies depending on the underlying type of curve.
#     #         nurbsCurve3D : Optional[adsk.core.NurbsCurve3D] = None
            
#     #         print('curve.objectType: ' + curve.objectType)
            
#     #         if False:
#     #             if curve.objectType == 'adsk::core::Arc3D':
#     #                 nurbsCurve3D = curve.asNurbsCurve
#     #             elif curve.objectType == 'adsk::core::Circle3D':
#     #                 nurbsCurve3D = curve.asNurbsCurve
#     #             elif curve.objectType == 'adsk::core::Ellipse3D':
#     #                 nurbsCurve3D = curve.asNurbsCurve
#     #             elif curve.objectType == 'adsk::core::EllipticalArc3D':
#     #                 nurbsCurve3D = curve.asNurbsCurve
#     #             elif curve.objectType == 'adsk::core::InfiniteLine3D':
#     #                 nurbsCurve3D = None
#     #             elif curve.objectType == 'adsk::core::Line3D':
#     #                 nurbsCurve3D = curve.asNurbsCurve
#     #             elif curve.objectType == 'adsk::core::NurbsCurve3D':
#     #                 nurbsCurve3D = curve
#     #             else:
#     #                 # I would be very surprised if we ever got here.
#     #                 pass

#     #         #perhaps the more pythonic way to do this would be to simply look for the presence of an asNurbsCurve property and take that
#     #         # property if it exists, else take the curve itself
#     #         nurbsCurve3D = getattr(curve, 'asNurbsCurve', curve)
#     #         if nurbsCurve3D:
#     #             edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(nurbsCurve3D) 

#     #         edgeHighlightingSketch.areProfilesShown = False

#     # if doBodyBasedHighlight:
#     #     if wireBodyToHighlight:
#     #         newlyCreatedPersistentBrepBody : adsk.fusion.BRepBody = mainOccurrence.component.bRepBodies.add(wireBodyToHighlight)
#     #         newlyCreatedPersistentBrepBody.name = 'wireBodyToHighlight'
#     #         print('bool(newlyCreatedPersistentBrepBody): ' + str(bool(newlyCreatedPersistentBrepBody)))
#     #         # in the case where the curves are disjoint, I would expect that wireBodyToHighlight and 
#     #         # newlyCreatedPersistentBrepBody would both be null, because Fusion tends to enforce that a body must be 
#     #         # contiguous.  However, curiously, in this case, both newlyCreatedPersistentBrepBody and wireBodyToHighlight are non-null,
#     #         # and a node appears in the 'bodies' folder in the tree in the UI, but the body does not appear to be visible graphically. 
#     #         # Even in the case where the wire body is not disjoint, the body does not appear graphically, although a node is added to the 
#     #         # bodies folder in the tree, and if we do the 'find in window' command in the ui, fusion does correctly zoom
#     #         #  the view to focus on the (invisible) wire body.  So, it seem,s that fusion is dealing with the wire body property in every way except actually
#     #         # displaying it in any way on screen.
#     #         # Does fusion allow persistent bodies that are wire bodies?  Or, a more meaningful question for my present goal: will fusion display on screen
#     #         # a wire body?

#     # if doCustomGraphicsBRepBodyBasedHighlight:
#     #     if wireBodyToHighlight:
#     #         customGraphicsGroup = rootComponent.customGraphicsGroups.add()
#     #         customGraphicsBRepBody = customGraphicsGroup.addBRepBody(wireBodyToHighlight)
#     #         app().activeViewport.refresh()
#     #     # no errors are thrown, but there appears to be no visible on-screen representation of the wire body.

#     if doCustomGraphicsCurveBasedHighlight:
#         customGraphicsGroup = rootComponent.customGraphicsGroups.add()

#         # customGraphicsGroup.color = preferredCustomGraphicsColorEffect
#         # the color property of the customGraphicsGroup appears to have no effect on the displayed color of the graphics entities within the group,
#         # regardless of whether we set the group's color property before or after adding the entities to it.
#         # This is true at least in my case, where preferredCustomGraphicsColorEffect is a CustomGraphicsSolidColorEffect 
#         # and where the entities in the custom graphics group are CustomGraphicsCurve objects.
#         # In order to achieve the desired display color, we must assign the color directly to the leaf entities.

#         customGraphicsCurves : Sequence[ Optional[adsk.fusion.CustomGraphicsCurve] ] = ( customGraphicsGroup.addCurve(curve) for curve in curvesToHighlight )
#         for customGraphicsCurve in customGraphicsCurves:
#             customGraphicsCurve.weight=preferredWeight
#             customGraphicsCurve.color=preferredCustomGraphicsColorEffect
#         # app().activeViewport.refresh() # this does not appear to have any effect, nor to be necessary

#     # do the custom graphics groups have to go in the root component?  I am thinking that if we put a custom grpahics group in a child component, then 
#     # perhaps we would be able, in the ui, to toggle the display of the graphics by toggling the visbility of the component that contains the custom graphics group.
#     # it is a bit odd that Fusion does not have custom graphics being first-class citizens in the UI (with the user able to control their visibility directly).  
#     # Perhaps the idea are that custom graphics are something that only makes sense in the context of an add-in, and
#     # therefore all user interaction with custom graphics is to be mediated by the add-in.
#     # It is also a bit odd that Fusion (I think) does
#     # not fully support wire bodies and point bodies in the UI.

#     # TODO: Extend the highlighting logic to handle more types of objects beyond just edges and curves: points, faces, solids, any brep body, occurrences, fscad components ...






    
    
#     # the types of things that can be custom graphics are 
#     # BRepBody 
#     #   apparently with the same limitations as 
#     #   BRepBodys within the model, namely, the BRepBody must be a solid or a surface (and possibly also must be contiguous) 
#     #   in order for Fusion to display it on the screen.  This means that wire bodies, and proboably also point bodies,
#     #   will not show up on the screen (although they may not cause any kind of formal exception or error).
#     # Curve
#     # Line
#     # Mesh
#     # PointSet
#     # Text
#     # Group (this is the "branch" node type in a tree structure where the leaves are things whose type is one of the aforementioned types.).
#     # Note specifically that the various parts of brep bodies (edge, face, etc.) cannot directly be made into custom graphics.
#     # If you want to highlight an edge, you have to pull out the underlying Curve3D, and make the curve a CustomGraphicsCurve object based on the Curve3D.
    
#     for entity in entities:
#         if isinstance(entity, adsk.fusion.Occurrence):
#             #not yet supported
#             pass
#         elif isinstance(entity, adsk.fusion.BRepBody):
#             #not yet supported
#             entity
#             pass
#         elif isinstance(entity, fscad.Edge):
#             # entity :  fscad.Edge = entity
#             # pylance seems to be smart enough not to need the above line for type inference
#             highlightEntities([entity.brep])
#         elif isinstance(entity, adsk.fusion.BRepEdge):
#             # entity = adsk.fusion.BRepEdge.cast(entity)
#             # pylance seems to be smart enough not to need the above line for type inference.  I am not sure if there would be any other advantage to doing a adsk.fusion.BRepEdge.cast()
#             if _customGraphicsGroupToReceiveTheCustomGraphics:
#                 customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
#             else:
#                 #figure out which component we want to add custom graphics to
#                 componentToReceiveTheCustomGraphics : adsk.fusion.Component = 

#                 # retrieve, or create, the customGraphicsGroup within componentToReceiveCustomGraphics.customGraphicsGroups (possibly a sub... group) to which we will add the customGraphicsEntity
#                 # should we add a new customGraphicsGroup for each edge to be highlighted? probably not.  However, for simplicity of the code, I will, at the moment, adopt this strategy.
#                 # should we simply use the first customGraphicsGroup in componentToReceiveCustomGraphics.customGraphicsGroups (creating it if it does not exist)
#                 # should we have one special customGraphicsGroup in each component that is dedicated to containing our custom graphics highlighting entities?  Something along these lines is probably the correct answer, but 
#                 # I will defer implementing such a system for now (mainly because it would be a bit of work to figure out how to keep track of and retrieve/create the special custom graphics group.
#                 # I do not understand how graphics groups are meant to be used.  Presumably, the intent is to set up some sort of cascading inheritance structure for graphical properties, so 
#                 # that properties assigned to a group will become the defaults for all then members of the group.
#                 customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()

#             highlightEntities([entity.geometry])


            
#         elif isinstance(entity, adsk.core.Curve3D):
#             ewrt
#         else:
#             #this is a type error
#endregion DEPRECATED_HIGHLIGHTING

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass
