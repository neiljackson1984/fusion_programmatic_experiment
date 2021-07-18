from scripted_component import *
import math


class Bolt (ScriptedComponent):
    defaultBoltName         = 'Bolt'
    defaultHeadDiameter     = 1.2
    defaultShankDiameter    = 0.4
    defaultHeadHeight       = 1
    defaultLength           = 4.0
    defaultCutAngle         = 30.0 * (math.pi / 180)
    defaultChamferDistance  = 0.06
    defaultFilletRadius     = 0.02994
        
    
    
    def __init__(self, fusionComponent: adsk.fusion.Component):
        super().__init__(fusionComponent)

        self._boltName         = Bolt.defaultBoltName
        self._headDiameter     = Bolt.defaultHeadDiameter
        self._shankDiameter    = Bolt.defaultShankDiameter
        self._headHeight       = Bolt.defaultHeadHeight
        self._length           = Bolt.defaultLength #adsk.core.ValueInput.createByReal(Bolt.defaultLength)
        self._cutAngle         = Bolt.defaultCutAngle
        self._chamferDistance  = Bolt.defaultChamferDistance #adsk.core.ValueInput.createByReal(Bolt.defaultChamferDistance)
        self._filletRadius     = Bolt.defaultFilletRadius #adsk.core.ValueInput.createByReal(Bolt.defaultFilletRadius)
        

    #properties
    @property
    def boltName(self):
        return self._boltName
    @boltName.setter
    def boltName(self, value):
        self._boltName = value

    @property
    def headDiameter(self):
        return self._headDiameter
    @headDiameter.setter
    def headDiameter(self, value):
        self._headDiameter = value

    @property
    def shankDiameter(self):
        return self._shankDiameter
    @shankDiameter.setter
    def shankDiameter(self, value):
        self._shankDiameter = value 

    @property
    def headHeight(self):
        return self._headHeight
    @headHeight.setter
    def headHeight(self, value):
        self._headHeight = value 

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, value):
        self._length = value   

    @property
    def cutAngle(self):
        return self._cutAngle
    @cutAngle.setter
    def cutAngle(self, value):
        self._cutAngle = value  

    @property
    def chamferDistance(self):
        return self._chamferDistance
    @chamferDistance.setter
    def chamferDistance(self, value):
        self._chamferDistance = value

    @property
    def filletRadius(self):
        return self._filletRadius
    @filletRadius.setter
    def filletRadius(self, value):
        self._filletRadius = value

    def update(self):
        self._update(constructFromScratch = False)

    # # static function to create a new class-backed component and return the 
    # # (newly-created) class instance
    # # def create(parentComponent: adsk.fusion.Component) -> Bolt: 
    # #oops:  >>   NameError: name 'Bolt' is not defined
    # # not sure the right way to type-hint this.
    # def create(parentComponent: adsk.fusion.Component):
    #     global attributeGroupName
    #     newlyCreatedOccurence  = parentComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    #     newlyCreatedComponent = adsk.fusion.Component(newlyCreatedOccurence.component)
    #     newlyCreatedComponent.attributes.add(attributeGroupName, "class_backed_component", "")
    #     newlyCreatedComponent.attributes.add(attributeGroupName, "class", "Bolt")
    #     newlyCreatedComponent.name = "{0.hour}{0.minute}{0.second}".format(datetime.datetime.now()) + " " + "bolt"
    #     newlyCreatedClassInstance = Bolt(newlyCreatedComponent)
    #     newlyCreatedClassInstance._update(constructFromScratch=True)
    #     return newlyCreatedClassInstance

    def _update(self, constructFromScratch: bool = False):
        theComponent: adsk.fusion.Component = self._fusionComponent
        printDebuggingMessage("updateBolt() is running with constructFromScratch=" + str(constructFromScratch) + ", and theComponent.name=" + theComponent.name)
        

        timestamp = "{0.hour}{0.minute}{0.second}".format(datetime.datetime.now())
        
        # we want to be able to do something here that looks like declaring the construction recipe.  For instance: "there is (shall be) a sketch, called
        # headSketch, that contains 6 lines (or, perhaps, that contains one closed path)...
        # We can certainly write the code to construct the sketch, then the extrusion, etc., but we want to not only construct the elements initially, but also to
        # "update" them in the future.  Now, we could certainly delete and re-create everything, but the goal is to maintain the internal identities that Fusion
        # assigns to the geometric elements, and deleting and recreating would wipe out any sense of identity that Fusion had already assigned (and, annoyingly, we 
        # cannot directly control Fusion's internal identity-assignment system).  Therefore, we must carefully look for and edit the existing features (or create them
        # if they do not already exist.  We are missing OnShape's elegant partially-user-controllable identity assignment system wherein the user assigns each feature an id
        # (an arbitrary string), and the id of an edge or a face, etc. is some magical composite of the ids of all the features that contributed to it.


        # So, in the case of the sketch for instance, we want a makeSketch function that takes an id parameter, and returns the sketch designated by that id (creating it if
        # it does not exist), and an analogous function for each thing that we want to create/update.  Ideally, we would want this system to be able to handle an exisintg component 
        # that is based on a radically different design than the code is currently designed to produce, so that we can take a component that has some extra elements, some missing elements, 
        # some re-arranged elements (as we might encounter when the design has changed), and we can "update" that component, to the new design in the most identity-preserving way
        # possible (The fallback strategy always being to delete and recreate everything).


        doBaseFeature = False

        if doBaseFeature:
            baseFeature = theComponent.features.baseFeatures.add()
            baseFeature.name = timestamp + " " + self.boltName
            baseFeature.startEdit()

        # if not constructFromScratch:
        #     savedReferences = theComponent.attributes.itemByName(attributeGroupName, "savedReferences")
        
        
        if constructFromScratch: 
            # Create headSketch - a sketch containing 6 lines
            headSketch = theComponent.sketches.add(theComponent.xYConstructionPlane)
            headSketch.attributes.add(attributeGroupName, "headSketch", "")

            # printDebuggingMessage("headSketch.attributes.groupNames: " + repr(headSketch.attributes.groupNames ) )
            # printDebuggingMessage("attributes of headSketch: " + 
            #     repr(
            #         [   
            #             attribute.groupName  + "." + attribute.name + ": " + attribute.value
            #             for attribute in headSketch.attributes
            #         ]
            #     )            
            # )

            headSketch.name=timestamp + " " + "head sketch"
            for i in range(0, 6):
                headSketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1, 1, 0))
            
            #create shankSketch - a sketch containing a circle
            shankSketch = theComponent.sketches.add(theComponent.xYConstructionPlane)
            shankSketch.attributes.add(attributeGroupName, "shankSketch", "")
            shankSketch.name=timestamp + " " + "shank sketch"

            shankSketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1)


        # find the headSketch and shankSketch
        # headSketch  = adsk.fusion.Sketch.cast( adsk.core.Attribute.cast( next(findAttributesInComponent(theComponent, attributeGroupName, "headSketch"))[0] ).parent )
        headSketch  = adsk.fusion.Sketch.cast( ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "headSketch") )
        shankSketch = adsk.fusion.Sketch.cast( ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "shankSketch") )
    
        center = adsk.core.Point3D.create(0, 0, 0)
        vertices = [
            adsk.core.Point3D.create(center.x + (self.headDiameter/2) * math.cos(math.pi * i / 3), center.y + (self.headDiameter/2) * math.sin(math.pi * i / 3),0)
            for i in range(0,6)
        ]

        for i in range(0, 6):
            thisLine = headSketch.sketchCurves.sketchLines.item(i)
            thisLine.startSketchPoint.move(thisLine.startSketchPoint.geometry.vectorTo(vertices[(i+1) %6]) )
            thisLine.endSketchPoint.move(thisLine.endSketchPoint.geometry.vectorTo(vertices[i]) )  
        
        shankCrossSectionCircle = adsk.fusion.SketchCircle.cast(shankSketch.sketchCurves.sketchCircles[0])
        shankCrossSectionCircle.centerSketchPoint.move(shankCrossSectionCircle.centerSketchPoint.geometry.vectorTo(center))
        shankCrossSectionCircle.radius = self.shankDiameter/2

        #we might also consider enforcing that headSketch and shankCrossSection have the xy plane as their sketch plane.

        if constructFromScratch: 
            headExtrusionInput = theComponent.features.extrudeFeatures.createInput(headSketch.profiles[0], adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            headExtrusionInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1))
            headExtrusion = theComponent.features.extrudeFeatures.add(headExtrusionInput)
            headExtrusion.attributes.add(attributeGroupName, "headExtrusion", "")
            headExtrusion.name = timestamp + " " + "head extrusion"
            headExtrusion.faces[0].body.name = timestamp + " " + self.boltName
        
        headExtrusion = adsk.fusion.ExtrudeFeature.cast(ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "headExtrusion"))
        
        headExtrusion.timelineObject.rollTo(True)
        # headExtrusion.setDistanceExtent( False, adsk.core.ValueInput.createByReal(self.headHeight) )
        # see the comment below when setting the chamfer distance, about not wanting to create a new parameter but instead set the value of the existing parameter.
        #as a test, I tried using the above ValueInput() strategy instead of the below parameter-value-modifying strategy.  Curiously, in the test, everything worked exactly as desired.
        # 
        adsk.fusion.DistanceExtentDefinition.cast(headExtrusion.extentOne).distance.value = self.headHeight

        theComponent.parentDesign.timeline.moveToEnd()
        #or, alternatively, might do headExtrusion.timelineObject.rollTo(False (we don't need to roll al the way to the end, just to the right of the headExtrusion feature.)

        if constructFromScratch: 
            shankExtrusionInput = theComponent.features.extrudeFeatures.createInput(shankSketch.profiles[0], adsk.fusion.FeatureOperations.JoinFeatureOperation)
            shankExtrusionInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1))
            shankExtrusionInput.participantBodies = list(headExtrusion.bodies)
            shankExtrusion = theComponent.features.extrudeFeatures.add(shankExtrusionInput)
            shankExtrusion.name = timestamp + " " + "shank extrusion"
            shankExtrusion.attributes.add(attributeGroupName, "shankExtrusion", "")

        shankExtrusion = adsk.fusion.ExtrudeFeature.cast(ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "shankExtrusion"))
        shankExtrusion.timelineObject.rollTo(True)
        shankExtrusion.participantBodies = list(headExtrusion.bodies)
        # shankExtrusion.setDistanceExtent(False, adsk.core.ValueInput.createByReal(self.length))
        # see the comment below when setting the chamfer distance, about not wanting to create a new parameter but instead set the value of the existing parameter.
        adsk.fusion.DistanceExtentDefinition.cast(shankExtrusion.extentOne).distance.value = self.length
        

        theComponent.parentDesign.timeline.moveToEnd()
        # printDebuggingMessage("shankSketch.attributes.groupNames: " + repr(shankSketch.attributes.groupNames))

        # create chamfer
        # edgeCollection = adsk.core.ObjectCollection.create() 
        # for edge in shankExtrusion.endFaces[0].edges: edgeCollection.add(edgeI)
        # chamferInput = theComponent.features.chamferFeatures.createInput(edgeCollection, True)
        
        #edgeCollection = adsk.core.ObjectCollection.cast(shankExtrusion.endFaces[0].edges)
        # the above casting does not work
        #  
        edgeCollection = adsk.core.ObjectCollection.create() 
        for edge in shankExtrusion.endFaces[0].edges: edgeCollection.add(edge)

        # printDebuggingMessage("edgeCollection.count: " + str(edgeCollection.count))

        if constructFromScratch:
            chamferInput = theComponent.features.chamferFeatures.createInput(edgeCollection, True)
            chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal(self.chamferDistance))
            #is it possible to add a chamfer feature without specifying any edges or any of the distance properties?  Will fusion let me add a non-buildable feature programmatically
            # (it certainly will not let me add one via the ui, but for our purposes here, we would like to add a non-buildable chamfer feature initially, and then set its properties later.
            # Adding the chamfer is the essence of what we do uniquely when we are consturcting from scratch, whereas setting the properties of the chamfer is something we will do every time.) 
            chamfer = theComponent.features.chamferFeatures.add(chamferInput)
            chamfer.attributes.add(attributeGroupName, "chamfer", "")
            chamfer.name = timestamp + " " + "chamfer"
        chamfer = adsk.fusion.ChamferFeature.cast(ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "chamfer"))
        chamfer.timelineObject.rollTo(True)

        #in the case where we are not construction from scratch, edgeCollection computed above
        # will contain an edge (on the chamfer) that does not exist before the chamfer was made, so we can not use it as in input for the
        # chamfer.  Hence, only now that we have rolled back the chamfer can we compute edgeCollection for the chamfer.
        edgeCollection = adsk.core.ObjectCollection.create() 
        for edge in shankExtrusion.endFaces[0].edges: edgeCollection.add(edge)

        # printDebuggingMessage("edgeCollection.count: " + str(edgeCollection.count))
        # edgeCollection = adsk.core.ObjectCollection.create() 
        # for edge in shankExtrusion.endFaces[0].edges: edgeCollection.add(edge)
        
        chamfer.edges = edgeCollection
        chamfer.isTangentChain = True
        
        # chamfer.setEqualDistance(adsk.core.ValueInput.createByReal(self.chamferDistance))
        # The above call to adsk.core.ValueInput.createByReal() (commented out) would create a new parameter every time we update, 
        # which is not what we want, and I am not even sure that Fusion would allow it (I suspect that parameters can only be created when you are creating a feature)
        adsk.fusion.EqualDistanceChamferTypeDefinition.cast(chamfer.chamferTypeDefinition).distance.value = self.chamferDistance
        theComponent.parentDesign.timeline.moveToEnd()

        # create fillet
        
        # edgeLoop = None
        # for edgeLoop in headExtrusion.endFaces[0].loops:
        #     #since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
        #     if(len(edgeLoop.edges) == 1):
        #         break
        
        # there two edgeloops in the start face of head: one that consists of one circle edge while the other has six edges.  We want the eddgeloop that has six edges.
        edgeLoop = next(
            filter(
                lambda loop: len(loop.edges) != 1,
                headExtrusion.endFaces[0].loops
            )
        )

        # edgeCollection = adsk.core.ObjectCollection.cast([edgeLoop.edges[0]])
        #the above casting does not work

        edgeCollection = adsk.core.ObjectCollection.create()  
        for edge in edgeLoop.edges: edgeCollection.add(edge)


        if constructFromScratch:
            filletInput = theComponent.features.filletFeatures.createInput()
            filletInput.addConstantRadiusEdgeSet(edgeCollection, adsk.core.ValueInput.createByReal(self.filletRadius), True)
            fillet = theComponent.features.filletFeatures.add(filletInput)
            fillet.attributes.add(attributeGroupName, "fillet", "")
            fillet.name = timestamp + " " + "fillet"
        fillet = adsk.fusion.FilletFeature.cast(ScriptedComponent.findFirstTaggedEntityInComponent(theComponent, "fillet"))
        fillet.timelineObject.rollTo(True)
        
        edgeLoop = next(
            filter(
                lambda loop: len(loop.edges) != 1,
                headExtrusion.endFaces[0].loops
            )
        )
        
        edgeCollection = adsk.core.ObjectCollection.create()  
        for edge in edgeLoop.edges: edgeCollection.add(edge)

        constantRadiusFilletEdgeSet = adsk.fusion.ConstantRadiusFilletEdgeSet.cast(fillet.edgeSets[0])
        constantRadiusFilletEdgeSet.edges = edgeCollection
        
        # constantRadiusFilletEdgeSet.isTangentChain = True
        #oops, that property does not exist -- are fillets half-baked?
        constantRadiusFilletEdgeSet.radius.value = self.filletRadius
        
        theComponent.parentDesign.timeline.moveToEnd()
        printDebuggingMessage("finished updating " + theComponent.name)

        # #create revolve feature 1
        # revolveSketch = theComponent.sketches.add(theComponent.xZConstructionPlane)
        # revolveSketch.name=timestamp + " " + "revolve sketch"
        # radius = self.headDiameter/2
        # point1 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius*math.cos(math.pi/6), 0, center.y))
        # point2 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius, 0, center.y))

        # point3 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(point2.x, 0, (point2.x - point1.x) * math.tan(self.cutAngle)))
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point1, point2)
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point2, point3)
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point3, point1)

        # #revolve feature 2
        # point4 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius*math.cos(math.pi/6), 0, self.headHeight - center.y))
        # point5 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius, 0, self.headHeight - center.y))
        # point6 = revolveSketch.modelToSketchSpace(adsk.core.Point3D.create(center.x + point2.x, 0, self.headHeight - center.y - (point5.x - point4.x) * math.tan(self.cutAngle)))
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point4, point5)
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point5, point6)
        # revolveSketch.sketchCurves.sketchLines.addByTwoPoints(point6, point4)

        # revolve1Profile = revolveSketch.profiles[0]
        # revolve1Input = theComponent.features.revolveFeatures.createInput(revolve1Profile, theComponent.zConstructionAxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # revolveAngle = adsk.core.ValueInput.createByReal(math.pi*2)
        # revolve1Input.setAngleExtent(False,revolveAngle)
        # revolve1 = theComponent.features.revolveFeatures.add(revolve1Input)
        # revolve1.name = timestamp + " " + "revolve1"

        # revolve2Profile = revolveSketch.profiles[1]
        # revolve2Input = theComponent.features.revolveFeatures.createInput(revolve2Profile, theComponent.zConstructionAxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # revolve2Input.setAngleExtent(False,revolveAngle)
        # revolve2 = theComponent.features.revolveFeatures.add(revolve2Input)
        # revolve2.name = timestamp + " " + "revolve2"

        # sideFace = shankExtrusion.sideFaces[0]
        # threadDataQuery = theComponent.features.threadFeatures.threadDataQuery
        # defaultThreadType = threadDataQuery.defaultMetricThreadType
        # recommendData = threadDataQuery.recommendThreadData(self.shankDiameter, False, defaultThreadType)
        # if recommendData[0] :
        #     threadInfo = theComponent.features.threadFeatures.createThreadInfo(False, defaultThreadType, recommendData[1], recommendData[2])
        #     faces = adsk.core.ObjectCollection.create()
        #     faces.add(sideFace)
        #     threadInput = theComponent.features.threadFeatures.createInput(faces, threadInfo)
        #     thread = theComponent.features.threadFeatures.add(threadInput)
        #     thread.name = timestamp + " " + "thread"
        # if doBaseFeature: baseFeature.finishEdit()
