import os, sys
import adsk.core, adsk.fusion, traceback
import inspect
import pprint
from typing import Optional, Sequence, Union

# sys.path.append(os.path.join(os.path.dirname(__file__)))
from . import scripted_component
from .scripted_component import ScriptedComponent
from .bolt import Bolt
from .braids.fscad.src.fscad import fscad as fscad






def app() -> adsk.core.Application: return adsk.core.Application.get()
def ui() -> adsk.core.UserInterface: return app().userInterface

def run(context:dict):
    # a = 3 + 3
    # pass
    # raise Exception("xxxbogus exception")
    # return
    
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
        holeTool.rotate(rx=27).rotate(rz=80).translate(tz=1)

        
        base = fscad.Difference(box, holeTool)

        y = fscad.RegularPolygon(5, 3.2, is_outer_radius=False)

        base = fscad.Group((base, y))

        mainOccurence = base.create_occurrence(create_children=True, scale=1)

        # I would like to be able to pick out the edges within base adjacent to any face that was present in box,
        # and that were newly created as a result of the Difference operation.  Thinking of the Difference operation
        # as drilling a blind hole, the edges I am interested in are the "lip" of the hole.
        # How can I pick out these edges?
        # One idea is to, before doing the Difference, tag all of the faces and edges of box (with
        # a tagging system that will preserve tags across body-modifying operations).  Then, after the difference operation,
        # I pick out untagged edges of the tagged faces -- these have to be the newly-created edges that I am interested in.

        # adsk.fusion.BRepBody.findByTempId
        # adsk.fusion.Design.findEntityByToken

        # adsk.fusion.BRepEdge.tempId 
        # # Returns the temporary ID of this edge. 
        # # This ID is only good while the document remains open and 
        # # as long as the owning BRepBody is not modified in any way. 
        # # The findByTempId method of the BRepBody will return the entity 
        # # in the body with the given ID.

        # adsk.fusion.BRepEdge.entityToken
        # # Returns a token for the BRepEdge object. 
        # # This can be saved and used at a later time with the 
        # # Design.findEntityByToken method to get back the same edge. When 
        # # using entity tokens it's important to understand that the token 
        # # string returned for a specific entity can be different over time. 
        # # However, even if you have two different token strings that were 
        # # obtained from the same entity, when you use findEntityByToken they 
        # # will both return the same entity. Because of that you should never 
        # # compare entity tokens as way to determine what the token represents.
        # # Instead, you need to use the findEntityByToken method to get the 
        # # two entities identified by the tokens and then compare them. This 
        # # is only valid for edges that exist in the design, 
        # # (the isTemporary property is false).

        # # BRepFace  has the same tempId and entityToken properties.
        
        edgesToHighlight : Sequence[fscad.Edge] = base.bodies[0].edges[0:2]
        # curvesToHighlight : Sequence[adsk.core.Curve3D] = [ x.brep.geometry for x in edgesToHighlight  ]
        # temporaryBRepManager : adsk.fusion.TemporaryBRepManager = adsk.fusion.TemporaryBRepManager.get()
        # (wireBodyToHighlight, edgeMap) = temporaryBRepManager.createWireFromCurves(curvesToHighlight)
        # print('bool(wireBodyToHighlight): ' + str(bool(wireBodyToHighlight)))
        # rootComponent = mainOccurence.component.parentDesign.rootComponent
        highlight(edgesToHighlight)
        
    # adsk.fusion.Design.cast(app().activeProduct).designType = adsk.fusion.DesignTypes.DirectDesignType
    # fscad requires that designType be DirectDesignType, not ParametricDesignType.  If you attempt to
    # run fscad's create_occurence() function when designType is ParametricDesignType, the result will be 
    # the error: "RuntimeError: 3 : A valid targetBaseFeature is required"
    # my_design()

    fscad.run_design(design_func=my_design, message_box_on_error=False)


    

    print("finished creating new bolts")
    # ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    # prevent this module from being terminated when the script returns
    # adsk.autoTerminate(False)

HighlightableThing = (
        Union[
            adsk.fusion.BRepEdge, 
            adsk.core.Curve3D, 
            adsk.fusion.BRepBody, 
            adsk.fusion.Occurrence, 
            fscad.BRepEntity
        ]
    )

def highlight(
    x: Union[HighlightableThing, Sequence[HighlightableThing]],
    _customGraphicsGroupToReceiveTheCustomGraphics : Optional[adsk.fusion.CustomGraphicsGroup] = None
    ):

    if xIsASequenceOfHighlightableThing:
        for y in x: highlight(y)
        return

    #at this point, it is safe to assume that x is a HighlightableThing
    highlightableThing : HighlightableThing = x

    preferredWeight = 3
    preferredColor  = adsk.core.Color.create(red=255, green=0, blue=0, opacity=255)
    preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)

    if isinstance(highlightableThing, adsk.fusion.Occurrence):
        occurence : adsk.fusion.Occurrence = highlightableThing
        #not yet supported
        
    elif isinstance(highlightableThing, adsk.fusion.BRepBody):
        brepBody : adsk.fusion.BRepBody = highlightableThing
        #not yet supported

    elif isinstance(highlightableThing, fscad.Edge):
        edge : fscad.Edge = highlightableThing
        # pylance seems to be smart enough not to need the above line for type inference, but I want it for my own sanity.
        highlight(edge.brep)

    elif isinstance(highlightableThing, adsk.fusion.BRepEdge):
        bRepEdge : adsk.fusion.BRepEdge = highlightableThing
        # is there any value to doing a adsk.fusion.BRepEdge.cast()?
        # entity = adsk.fusion.BRepEdge.cast(entity)
        # pylance seems to be smart enough not to need the above line for type inference.  I am not sure if there would be any other advantage to doing a adsk.fusion.BRepEdge.cast()
        
        if _customGraphicsGroupToReceiveTheCustomGraphics:
            customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
        else:
            #figure out which component we want to add custom graphics to
            componentToReceiveTheCustomGraphics : adsk.fusion.Component = 

            if bRepEdge.assemblyContext:
                

            # retrieve, or create, the customGraphicsGroup within componentToReceiveCustomGraphics.customGraphicsGroups (possibly a sub... group) to which we will add the customGraphicsEntity
            # should we add a new customGraphicsGroup for each edge to be highlighted? probably not.  However, for simplicity of the code, I will, at the moment, adopt this strategy.
            # should we simply use the first customGraphicsGroup in componentToReceiveCustomGraphics.customGraphicsGroups (creating it if it does not exist)
            # should we have one special customGraphicsGroup in each component that is dedicated to containing our custom graphics highlighting entities?  Something along these lines is probably the correct answer, but 
            # I will defer implementing such a system for now (mainly because it would be a bit of work to figure out how to keep track of and retrieve/create the special custom graphics group.
            # I do not understand how graphics groups are meant to be used.  Presumably, the intent is to set up some sort of cascading inheritance structure for graphical properties, so 
            # that properties assigned to a group will become the defaults for all then members of the group.
            customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()

        highlight(bRepEdge.geometry, customGraphicsGroupToReceiveTheCustomGraphics)

    elif isinstance(highlightableThing, adsk.core.Curve3D):
        curve3D : adsk.core.Curve3D = highlightableThing

    else:
        #this is a type error




def highlightEntities(entities: Sequence[HighlightableThing], 
    
    _customGraphicsGroupToReceiveTheCustomGraphics : Optional[adsk.fusion.CustomGraphicsGroup] = None
    
    ):
    # how to graphically highlight an arbitrary set of edges:

  
    doSketchBasedHighlight = False
    doBodyBasedHighlight = False 
    doCustomGraphicsBRepBodyBasedHighlight = False
    doCustomGraphicsCurveBasedHighlight = True

    preferredWeight=3
    preferredColor = adsk.core.Color.create(red=255, green=0, blue=0, opacity=255)
    preferredCustomGraphicsColorEffect : adsk.fusion.CustomGraphicsColorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(preferredColor)

    # if doSketchBasedHighlight:
    #     edgeHighlightingSketch : Optional[adsk.fusion.Sketch] = mainOccurence.component.sketches.add(mainOccurence.component.xYConstructionPlane)
    #     for curve in curvesToHighlight:
    #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(curve) # throws type error
    #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(adsk.core.NurbsCurve3D.cast(curve)) # throws RuntimeError: 3 : Invalid argument nurbsCurve
    #         # edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(adsk.core.NurbsCurve3D(curve)) # throws "no constructor defined" error.
            
    #         # convert the curve into a nurbsCurve3D object.
    #         # the conversion method varies depending on the underlying type of curve.
    #         nurbsCurve3D : Optional[adsk.core.NurbsCurve3D] = None
            
    #         print('curve.objectType: ' + curve.objectType)
            
    #         if False:
    #             if curve.objectType == 'adsk::core::Arc3D':
    #                 nurbsCurve3D = curve.asNurbsCurve
    #             elif curve.objectType == 'adsk::core::Circle3D':
    #                 nurbsCurve3D = curve.asNurbsCurve
    #             elif curve.objectType == 'adsk::core::Ellipse3D':
    #                 nurbsCurve3D = curve.asNurbsCurve
    #             elif curve.objectType == 'adsk::core::EllipticalArc3D':
    #                 nurbsCurve3D = curve.asNurbsCurve
    #             elif curve.objectType == 'adsk::core::InfiniteLine3D':
    #                 nurbsCurve3D = None
    #             elif curve.objectType == 'adsk::core::Line3D':
    #                 nurbsCurve3D = curve.asNurbsCurve
    #             elif curve.objectType == 'adsk::core::NurbsCurve3D':
    #                 nurbsCurve3D = curve
    #             else:
    #                 # I would be very surprised if we ever got here.
    #                 pass

    #         #perhaps the more pythonic way to do this would be to simply look for the presence of an asNurbsCurve property and take that
    #         # property if it exists, else take the curve itself
    #         nurbsCurve3D = getattr(curve, 'asNurbsCurve', curve)
    #         if nurbsCurve3D:
    #             edgeHighlightingSketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(nurbsCurve3D) 

    #         edgeHighlightingSketch.areProfilesShown = False

    # if doBodyBasedHighlight:
    #     if wireBodyToHighlight:
    #         newlyCreatedPersistentBrepBody : adsk.fusion.BRepBody = mainOccurence.component.bRepBodies.add(wireBodyToHighlight)
    #         newlyCreatedPersistentBrepBody.name = 'wireBodyToHighlight'
    #         print('bool(newlyCreatedPersistentBrepBody): ' + str(bool(newlyCreatedPersistentBrepBody)))
    #         # in the case where the curves are disjoint, I would expect that wireBodyToHighlight and 
    #         # newlyCreatedPersistentBrepBody would both be null, because Fusion tends to enforce that a body must be 
    #         # contiguous.  However, curiously, in this case, both newlyCreatedPersistentBrepBody and wireBodyToHighlight are non-null,
    #         # and a node appears in the 'bodies' folder in the tree in the UI, but the body does not appear to be visible graphically. 
    #         # Even in the case where the wire body is not disjoint, the body does not appear graphically, although a node is added to the 
    #         # bodies folder in the tree, and if we do the 'find in window' command in the ui, fusion does correctly zoom
    #         #  the view to focus on the (invisible) wire body.  So, it seem,s that fusion is dealing with the wire body property in every way except actually
    #         # displaying it in any way on screen.
    #         # Does fusion allow persistent bodies that are wire bodies?  Or, a more meaningful question for my present goal: will fusion display on screen
    #         # a wire body?

    # if doCustomGraphicsBRepBodyBasedHighlight:
    #     if wireBodyToHighlight:
    #         customGraphicsGroup = rootComponent.customGraphicsGroups.add()
    #         customGraphicsBRepBody = customGraphicsGroup.addBRepBody(wireBodyToHighlight)
    #         app().activeViewport.refresh()
    #     # no errors are thrown, but there appears to be no visible on-screen representation of the wire body.

    if doCustomGraphicsCurveBasedHighlight:
        customGraphicsGroup = rootComponent.customGraphicsGroups.add()

        # customGraphicsGroup.color = preferredCustomGraphicsColorEffect
        # the color property of the customGraphicsGroup appears to have no effect on the displayed color of the graphics entities within the group,
        # regardless of whether we set the group's color property before or after adding the entities to it.
        # This is true at least in my case, where preferredCustomGraphicsColorEffect is a CustomGraphicsSolidColorEffect 
        # and where the entities in the custom graphics group are CustomGraphicsCurve objects.
        # In order to achieve the desired display color, we must assign the color directly to the leaf entities.

        customGraphicsCurves : Sequence[ Optional[adsk.fusion.CustomGraphicsCurve] ] = ( customGraphicsGroup.addCurve(curve) for curve in curvesToHighlight )
        for customGraphicsCurve in customGraphicsCurves:
            customGraphicsCurve.weight=preferredWeight
            customGraphicsCurve.color=preferredCustomGraphicsColorEffect
        # app().activeViewport.refresh() # this does not appear to have any effect, nor to be necessary

    # do the custom graphics groups have to go in the root component?  I am thinking that if we put a custom grpahics group in a child component, then 
    # perhaps we would be able, in the ui, to toggle the display of the graphics by toggling the visbility of the component that contains the custom graphics group.
    # it is a bit odd that Fusion does not have custom graphics being first-class citizens in the UI (with the user able to control their visibility directly).  
    # Perhaps the idea are that custom graphics are something that only makes sense in the context of an add-in, and
    # therefore all user interaction with custom graphics is to be mediated by the add-in.
    # It is also a bit odd that Fusion (I think) does
    # not fully support wire bodies and point bodies in the UI.

    # TODO: Extend the highlighting logic to handle more types of objects beyond just edges and curves: points, faces, solids, any brep body, occurences, fscad components ...






    
    
    # the types of things that can be custom graphics are 
    # BRepBody 
    #   apparently with the same limitations as 
    #   BRepBodys within the model, namely, the BRepBody must be a solid or a surface (and possibly also must be contiguous) 
    #   in order for Fusion to display it on the screen.  This means that wire bodies, and proboably also point bodies,
    #   will not show up on the screen (although they may not cause any kind of formal exception or error).
    # Curve
    # Line
    # Mesh
    # PointSet
    # Text
    # Group (this is the "branch" node type in a tree structure where the leaves are things whose type is one of the aforementioned types.).
    # Note specifically that the various parts of brep bodies (edge, face, etc.) cannot directly be made into custom graphics.
    # If you want to highlight an edge, you have to pull out the underlying Curve3D, and make the curve a CustomGraphicsCurve object based on the Curve3D.
    
    for entity in entities:
        if isinstance(entity, adsk.fusion.Occurrence):
            #not yet supported
            pass
        elif isinstance(entity, adsk.fusion.BRepBody):
            #not yet supported
            entity
            pass
        elif isinstance(entity, fscad.Edge):
            # entity :  fscad.Edge = entity
            # pylance seems to be smart enough not to need the above line for type inference
            highlightEntities([entity.brep])
        elif isinstance(entity, adsk.fusion.BRepEdge):
            # entity = adsk.fusion.BRepEdge.cast(entity)
            # pylance seems to be smart enough not to need the above line for type inference.  I am not sure if there would be any other advantage to doing a adsk.fusion.BRepEdge.cast()
            if _customGraphicsGroupToReceiveTheCustomGraphics:
                customGraphicsGroupToReceiveTheCustomGraphics = _customGraphicsGroupToReceiveTheCustomGraphics
            else:
                #figure out which component we want to add custom graphics to
                componentToReceiveTheCustomGraphics : adsk.fusion.Component = 

                # retrieve, or create, the customGraphicsGroup within componentToReceiveCustomGraphics.customGraphicsGroups (possibly a sub... group) to which we will add the customGraphicsEntity
                # should we add a new customGraphicsGroup for each edge to be highlighted? probably not.  However, for simplicity of the code, I will, at the moment, adopt this strategy.
                # should we simply use the first customGraphicsGroup in componentToReceiveCustomGraphics.customGraphicsGroups (creating it if it does not exist)
                # should we have one special customGraphicsGroup in each component that is dedicated to containing our custom graphics highlighting entities?  Something along these lines is probably the correct answer, but 
                # I will defer implementing such a system for now (mainly because it would be a bit of work to figure out how to keep track of and retrieve/create the special custom graphics group.
                # I do not understand how graphics groups are meant to be used.  Presumably, the intent is to set up some sort of cascading inheritance structure for graphical properties, so 
                # that properties assigned to a group will become the defaults for all then members of the group.
                customGraphicsGroupToReceiveTheCustomGraphics = componentToReceiveTheCustomGraphics.customGraphicsGroups.add()

            highlightEntities([entity.geometry])


            
        elif isinstance(entity, adsk.core.Curve3D):
            ewrt
        else:
            #this is a type error


# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass