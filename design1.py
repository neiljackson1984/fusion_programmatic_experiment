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

    def design2():
        bitHolderSegment = bit_holder.BitHolderSegment()
        fscadComponent = bitHolderSegment.build()
        # fscadComponent.create_occurrence()

    fscad.run_design(design_func=design2, message_box_on_error=False)

    print("finished creating new bolts")
    #     ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    # prevent this module from being terminated when the script returns
    #     adsk.autoTerminate(False)

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass
