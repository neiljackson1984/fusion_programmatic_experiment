
import adsk.core, adsk.fusion
from typing import Optional, Iterable, Union
from .braids.fscad.src.fscad import fscad as fscad
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import tempfile
import uuid

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
    # at least for the case of BRepFace, BRepLoop, and BRepEdge, according to the documentation
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
            adsk.core.Point3D,
            fscad.BRepEntity,
            fscad.Component
        ])

def getOwningComponent(customGraphicsGroup : adsk.fusion.CustomGraphicsGroup) -> adsk.fusion.Component:
    returnValue = customGraphicsGroup.parent
    while not isinstance(returnValue, adsk.fusion.Component):
        returnValue = returnValue.parent
    return returnValue

def highlight(
    # x: Union[HighlightableThing, Iterable[HighlightableThing]],
    *args : Union[HighlightableThing, Iterable[HighlightableThing]],
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

    if _fallbackComponentToReceiveTheCustomGraphics is None:
        _fallbackComponentToReceiveTheCustomGraphics = adsk.fusion.Design.cast(adsk.core.Application.cast(adsk.core.Application.get()).activeProduct).rootComponent


    highlightableThing : HighlightableThing
    for arg in args:
        if isinstance(arg, Iterable):
            # this is not quite the test I want, because
            # because we could conceivably have some object (maybe) that is both a HighlightableThing and Iterable,
            # in which case I would want to first attempt to treat it as a HighlightableThing.
            for highlightableThing in arg: highlight(highlightableThing, _customGraphicsGroupToReceiveTheCustomGraphics=_customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)
            continue
        highlightableThing : HighlightableThing = arg

        preferredWeight = 3
        preferredColor : adsk.core.Color = adsk.core.Color.create(red=255, green=0, blue=0, opacity=255)
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
            
            
            #mainly for debugging, let's give bodies a different color from curves:
            preferredColor  = adsk.core.Color.create(red=255, green=0, blue=0, opacity=100)
            
            if True:
                preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)
            else:
                appearances = getOwningComponent(customGraphicsGroupToReceiveTheCustomGraphics).parentDesign.appearances
                appearance : adsk.core.Appearance = appearances.addByCopy(appearanceToCopy=appearances[0], name='fred-'+str(uuid.uuid4()))
                # (
                #     (appearanceProperty.id, appearanceProperty.name, appearanceProperty.objectType)
                #     for appearanceProperty in 
                #     appearance.appearanceProperties 
                # )
                for appearanceProperty in appearance.appearanceProperties :
                    if isinstance(appearanceProperty, adsk.core.ColorProperty):
                        for i in range(len(appearanceProperty.values)):
                            # appearanceProperty.values[i] =  adsk.core.Color.create(red=0, green=140, blue=0, opacity=100)
                            appearanceProperty.values[i].setColor(red=0, green=140, blue=0, opacity=100)
                        # appearanceProperty.values = [
                        #     adsk.core.Color.create(red=255, green=0, blue=0, opacity=100),
                        #     adsk.core.Color.create(red=0, green=255, blue=0, opacity=102)
                        # ]
                        
                        appearanceProperty.values = list(
                            # adsk.core.Color.create(red=0, green=140, blue=0, opacity=100)
                            preferredColor
                            for color in appearanceProperty.values
                        )
                preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsAppearanceColorEffect.create(appearance)
            
            customGraphicsGroupToReceiveTheCustomGraphics.color=preferredCustomGraphicsColorEffect
            customGraphicsBRepBody : Optional[adsk.fusion.CustomGraphicsBRepBody] = customGraphicsGroupToReceiveTheCustomGraphics.addBRepBody(bRepBody) 
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
        elif isinstance(highlightableThing, adsk.core.Point3D      ):
            point3D : adsk.core.Point3D = highlightableThing
            if _customGraphicsGroupToReceiveTheCustomGraphics is not None:
                customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
            elif _fallbackComponentToReceiveTheCustomGraphics is not None:
                componentToReceiveTheCustomGraphics : adsk.fusion.Component = _fallbackComponentToReceiveTheCustomGraphics
                customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()
            else:
                print("while attempting to highlight an adsk.core.Point3D, we are unable to determine which component in which to place the custom graphics, and therefore cannot proceed with the highlighting of this thing.")
                # this is an error, we cannot figure out which component to place the custom graphics entities, so we cannot proceed.
                return
            
            coordinates : adsk.fusion.CustomGraphicsCoordinates = adsk.fusion.CustomGraphicsCoordinates.create(point3D.asArray())
            coordinates.setColor(0,preferredColor)
            # coordinates.setCoordinate(0,point3D)
            # customGraphicsPointSet : Optional[adsk.fusion.CustomGraphicsPointSet] = customGraphicsGroupToReceiveTheCustomGraphics.addPointSet(
            #     coordinates=coordinates,
            #     indexList=[],
            #     pointType= adsk.fusion.CustomGraphicsPointTypes.PointCloudCustomGraphicsPointType ,
            #     pointImage=''
            # )
            img = Image.new(mode='RGB',size=(4, 4),color=(preferredColor.red, preferredColor.green, preferredColor.blue))
            pathOfPointImageFile=tempfile.mktemp('.png')          
            img.save(pathOfPointImageFile, format='png')
            
            #using an image file as the point icon is quite a hack.  It might be
            # better to do a sphere as brep bodies, and to use some of the scaling features built into
            # the custom graphics system so as to scale the sphere relative to the screen rather than relative to the model.
            customGraphicsPointSet : Optional[adsk.fusion.CustomGraphicsPointSet] = customGraphicsGroupToReceiveTheCustomGraphics.addPointSet(
                coordinates=coordinates,
                indexList=[],
                pointType= adsk.fusion.CustomGraphicsPointTypes.UserDefinedCustomGraphicsPointType ,
                pointImage=pathOfPointImageFile
            )
            customGraphicsPointSet.color = preferredCustomGraphicsColorEffect

        elif isinstance(highlightableThing, adsk.core.Surface       ): #NOT REALLY SUPPORTED, OR MEANINGFUL
            # it probably does not make sense to highlight a surface, because a
            # surface is unbounded (or not explicitly bounded) geometry. the
            # below technique will fail consistently because, at the moment, I
            # have not done anything to construct a useful set of loops for the
            # face.  adsk.core.  Surface  really should be not be considered a HighlightableThing.
            # This code dealing with Surface is left over from a time when I was under the false
            # impression that a surface was something like a face.
            
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
        elif isinstance(highlightableThing, fscad.Component    ):
            fscadComponent : fscad.Component = highlightableThing
            highlight(fscadComponent.bodies, _customGraphicsGroupToReceiveTheCustomGraphics=_customGraphicsGroupToReceiveTheCustomGraphics, _fallbackComponentToReceiveTheCustomGraphics=_fallbackComponentToReceiveTheCustomGraphics)

        else:
            print("We do not know how to highlight a " + str(type(highlightableThing)))
            
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