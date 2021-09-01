# this is a temporary file where I am adjusting the code  to port from featurescript to fusion/fscad, before copying
# working code into the real bit_holder file


from .bit_holder import *

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
        
        self.worldPlane = adsk.core.Matrix3D.create() # XY_PLANE
        # worldPlane might reasonably be called "transform".
        # internally, we think about doing the galley layout on the xy plane.
        
        # //the anchor specifies which point in galley space will be mapped to the origin of worldPlane.
        # // self.anchor may be any of the following:
        # //  a galleyAnchor_e enum value
        # //  a 3d length vector (according to is3dLengthVector()), in which case this will be taken as the point in galley space to be mapped to the origin of worldPlane
        # //  a unitless vector having at least 2 elements (Accordng to size() >= 2 and isUnitlessVector()), in which case the elements 
        # of self.anchor will taken to be a scale factor to be applied to width and height, respectively 
        # (in the spirit of the scaled position that Mathematica uses for many of its graphics functions)
        self.anchor = GalleyAnchor_e.BOTTOM_LEFT
        
        # //the text boxes will be aligned with the margin (which is a rectangular region that is inset from the edges of the galley according to the margin values above.

        self.text = ""
        # // self.fontName = "Tinos-Italic.ttf"
        # // self.fontHeight = 12/72 * inch   
    
    def buildSheetBodiesInGalleySpace(self):
        
        # //parse tex-style directives from the text.
        # regExPatternForTexDirective = re.compile(r"(?P<preceedingChunk>.*?)(\\(?P<controlWord>\w+)(\{(?P<argument>.*?)\}|))(?P<followingChunk>.*)")
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
        
        sheetBodiesInGalleySpace = []
        # //we will use sheetBodiesInGalleySpace as a container, which we willl fill up with sheet bodies.
        # //By the time we are done working, sheetBodiesInGalleySpace will contain all the the sheetBodies that we want.
        
        if floodWithInk:
            sheetBodiesInGalleySpace.append(
                # // rectangle from [0,0] to [self.width, self.height]
                FilledRectangle(
                    corner1=vector(zeroLength, zeroLength, zeroLength),
                    corner2=vector(self.width, self.height, zeroLength)
                ).buildSheetBodiesInGalleySpace()
            )
            
            # sheetBodiesInGalleySpace = qUnion([
            #         sheetBodiesInGalleySpace,
            #         # // rectangle from [0,0] to [self.width, self.height]  //thisTextRow[].buildSheetBodiesInGalleySpace(context, uniqueId(context, id))
            #         # new_filledRectangle({"corner1": vector(0,0) * meter, "corner2": vector(self.width, self.height)})[].buildSheetBodiesInGalleySpace(context, uniqueId(context, id))
            #     ])
            # //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
        else:
            # # // lay down the text boxes
            linesOfText = sanitizedText.split("\n")
            # # var initX
            # # var initY
            initZ = zeroLength
            
                                
            # # //the following three lines allow the fontName, rowHeight, and rowSpacing to be either arrays or single values.
            # # // if an array, we will cycle through the values in the array as we create one row after another.
            fontNameArray = (self.fontName if not isinstance(self.fontName, str) else [self.fontName])
            rowHeightArray = (self.rowHeight if isinstance(self.rowHeight, Sequence) else [self.rowHeight])
            rowSpacingArray = (self.rowSpacing  if isinstance(self.rowSpacing, Sequence) else [self.rowSpacing]) 
            #// the entries in the row spacing array affect how much space will
            #exist between a row and the row above it. (thus, row spacing for
            #the first row has no effect - only for rows after the first row.)
            
            # # //verticalRowInterval is the vertical distance that we will move the insertion point between successive rows.
            # # //var verticalRowInterval = self.rowHeight * self.rowSpacing; 
            
            
            # //heightOfAllText is the distance from the baseline of the bottom row to the ascent of the top row, when all rows are laid out.
            # //var heightOfAllText = verticalRowInterval * size(linesOfText);
            heightOfAllText = rowHeightArray[0]
            for i in range(1, len(linesOfText)): #(var i = 1; i<size(linesOfText); i+=1):
                # //self.rowHeight + (size(linesOfText)-1)*verticalRowInterval;
                heightOfAllText += rowSpacingArray[i % len(rowSpacingArray)] * rowHeightArray[i % len(rowHeightArray)]
            
            if  self.horizontalAlignment == HorizontalAlignment.LEFT:
                initX = self.leftMargin
            elif self.horizontalAlignment == HorizontalAlignment.CENTER:
                initX = mean( self.leftMargin, self.width - self.rightMargin )
            else: #// if (self.horizontalAlignment == HorizontalAlignment.RIGHT)
                initX = self.width - self.rightMargin

            if self.verticalAlignment == VerticalAlignment.TOP:
                initY = self.height - self.topMargin - rowHeightArray[0]
            elif self.verticalAlignment == VerticalAlignment.CENTER:
                initY = (
                    mean([self.height - self.topMargin, self.bottomMargin]) # //this is the y-coordinate of the vertical center
                    + heightOfAllText/2 
                    - self.rowHeight
                )
            else: # // if(  self.verticalAlignment == VerticalAlignment.BOTTOM )
                initY = self.bottomMargin + heightOfAllText - rowHeightArray[0]
            
            insertionPoint = vector(initX, initY , initZ)

            for i in range(len(linesOfText)): # (var i = 0; i<size(linesOfText); i+=1):  
                lineOfText = linesOfText[i]
                thisTextRow = TextRow(
                    owningGalley = self, 
                    text = lineOfText,
                    fontName = fontNameArray[i % len(fontNameArray)],
                    height = rowHeightArray[i % len(rowHeightArray)]
                )  
                
                if(  self.horizontalAlignment == HorizontalAlignment.LEFT ):
                        thisTextRow.basePoint = insertionPoint
                elif (self.horizontalAlignment == HorizontalAlignment.CENTER):
                        thisTextRow.basePoint = insertionPoint - thisTextRow.width/2 * vector(1, 0, 0)
                else: #// if(  self.horizontalAlignment == HorizontalAlignment.RIGHT )
                    thisTextRow.basePoint = insertionPoint - thisTextRow.width * vector(1, 0, 0)
                
                if i<len(linesOfText)-1: #//if we are not on the last row
                    insertionPoint += -yHat * rowSpacingArray[i+1 % len(rowSpacingArray)] * rowHeightArray[i+1 % len(rowHeightArray)] #//drop the insertion point down to be ready to start the next row.  
                
                sheetBodiesInGalleySpace.append(thisTextRow.buildSheetBodiesInGalleySpace())
        


        # //apply clipping, if requested.
        if self.clipping:         
            # //construct the galleyMask.  This is a region outside of which we will not allow the galley to have any effect.  
            # // (We will do a boolean intersection between galleyMask and the sheet bodies created above.
            
            # fCuboid(
            #     context,
            #     idOfGalleyMask,
            #     {
            #         corner1:vector(0,0,-1) * millimeter,
            #         corner2:vector(self.width , self.height , 1 * millimeter)
            #     }
            # )

            galleyMask = Cuboid(
                corner1=vector(0,0,-1) * millimeter,
                corner2=vector(self.width , self.height , 1 * millimeter)
            )

            # # //println("reportOnEntities(context,galleyMask,0): " ~ toString(reportOnEntities(context,galleyMask,0)));
            # # //debug(context, qOwnedByBody(sheetBodiesInGalleySpace, EntityType.FACE));
            # try:
            #     opExtrude(
            #         context,
            #         idOfTextExtrude,
            #         {
            #             # //entities:  sheetBodiesInGalleySpace,
            #             entities:  qOwnedByBody(sheetBodiesInGalleySpace, EntityType.FACE),
            #             direction: vector(0,0,1),
            #             endBound: BoundingType.BLIND,
            #             endDepth: 0.5 * millimeter,
            #             startBound: BoundingType.BLIND,
            #             startDepth: zeroLength
            #         }
            #     )
            # except error:
            #     # println("getFeatureError(context, idOfTextExtrude): " ~ getFeatureError(context, idOfTextExtrude));		# // getFeatureError(context, idOfTextExtrude);
            #     pass
            
            
            
            # textSolidBodies = qBodyType(qCreatedBy(idOfTextExtrude, EntityType.BODY), BodyType.SOLID)
            # # //debug(context, textSolidBodies);                    
            # # //debug(context, sheetBodiesInGalleySpace);
            # # //debug(context, galleyMask);
            # # //println("before clipping: reportOnEntities(context, textSolidBodies): " ~ reportOnEntities(context, textSolidBodies,0,0));		
            # # //println("before clipping: reportOnEntities(context, galleyMask): " ~ reportOnEntities(context, galleyMask,0,0));
            
            # if False: #//This doesn't work because the boolean intersection completely ignores the "targets" argument.
            #     # // It acts only on the tools.
            #     opBoolean(context, idOfClipping,
            #         {
            #             tools: galleyMask,
            #             targets: textSolidBodies,
            #             # ////targets: sheetBodiesInGalleySpace,
            #             operationType: BooleanOperationType.INTERSECTION,
            #             targetsAndToolsNeedGrouping:true,
            #             keepTools:true
            #         }
            #     ); 

            # opBoolean(
            #     context,
            #     idOfClipping,
            #     {
            #         tools: galleyMask,
            #         targets: textSolidBodies,
            #         # //targets: sheetBodiesInGalleySpace,
            #         operationType: BooleanOperationType.SUBTRACT_COMPLEMENT,
            #         targetsAndToolsNeedGrouping:false,
            #         keepTools:false
            #     }
            # )
            # # // // Counter-intuitively, the boolean SUBTRACT_COMPLEMENT operation (which relies on the boolean SUBTRACT operation 
            # # // // under the hood,
            # # // // and therefore this is probably also true for the SUBTRACT operation) essentially destroys all input bodies 
            # # // // and creates brand new bodies.  Therefore, we need to redefine the textSoidBodies query
            # # // // to be the set of solid bodies created by the clipping operation:
            # # // // textSolidBodies = qBodyType(qCreatedBy(idOfClipping, EntityType.BODY), BodyType.SOLID);
            # # // UPDATE: after updating from Featurescript version 626 to version 1271,
            # # // it seems that the boolean SUBTRAC_COMPLEMENT operation (and, presumably also the SUBTRACT operation)
            # # // now behaves intuitively and does not destroy all input bodies.  Therefore, it is no longer necessary
            # # // to redefine the textSolidBodies query to be the set of solid boides created by the clipping operation.
            # # // In fact, if we did now perform that re-definition, the newly defined textSolidBodies query would 
            # # // resolve to nothing, because the new version of the SUBTRACt_COMPLEMENT operation does not 'create' any solid
            # # // bodies - it merely modifies them.  (although perhaps it does create edges and faces where existing solid bodies are chopped
            # # // up.
    
            

            
            
            
            
            # # //println("after clipping: reportOnEntities(context, textSolidBodies): " ~ reportOnEntities(context, textSolidBodies,0,0));		
            # # //println("after clipping: reportOnEntities(context, galleyMask): " ~ reportOnEntities(context, galleyMask,0,0));
            # # //debug(context, qOwnedByBody(textSolidBodies, EntityType.EDGE));  
            # allFacesOfTextSolidBodies = qOwnedByBody(textSolidBodies,EntityType.FACE);
            # facesToKeep = qCoincidesWithPlane(allFacesOfTextSolidBodies, XY_PLANE);
            # facesToDelete = qSubtraction(allFacesOfTextSolidBodies, facesToKeep);
            # newEntitiesFromDeleteFace = startTracking(context, qUnion([textSolidBodies, allFacesOfTextSolidBodies]));
            
            # # //delete faces from allFacesOfTextSolidBodies that do not lie on the XY plane
            # idOfDeleteFace = uniqueId(context, id);
            # try silent{
            #     opDeleteFace(
            #         context,
            #         idOfDeleteFace,
            #         {
            #             deleteFaces: facesToDelete ,
            #             includeFillet:false,
            #             capVoid:false,
            #             leaveOpen:true
            #         }
            #     );
            #     # // this opDeleteFace will throw an excpetion when facesToDelete is empty (which happens when all the textSolidBodies lie entirely outside the galley mask.  That is the reason for the try{}.
                
            # } catch(error)
            # {
                
            # }
            # # //by deleting faces, the solid bodies will have become sheet bodies.
            # # // the opDeleteFace operation doesn't "create" any bodies (in the sense of OnShape id assignment), however it does seem to destroy all input bodies (at least in this case, where we are removing faces from a solid body to end up with a sheet body).  The only way I have found to retrieve the resultant sheet bodies is with a tracking query.  
            # clippedSheetBodiesInGalleySpace =                qBodyType(
            #         qOwnerBody(
            #             qEntityFilter(newEntitiesFromDeleteFace,EntityType.FACE)
            #         ), 
            #         BodyType.SHEET
            #     )
            
            # # //Not knowing exactly how the tracking query works, I am running the query through evaluateQuery() here for good measure, to make sure that I can use this query later on to still refer to preciesly the entities which exist at this point in the build history.            
            # clippedSheetBodiesInGalleySpace = qUnion(evaluateQuery(context, clippedSheetBodiesInGalleySpace));

            # if False:
            #     println("reportOnEntities(context, qCreatedBy(idOfDeleteFace),1,0): "      ~ "\n" ~ reportOnEntities(context, qCreatedBy(idOfDeleteFace),   1, 0));	
            #     println("reportOnEntities(context, textSolidBodies,1,0): "                 ~ "\n" ~ reportOnEntities(context, textSolidBodies,              1, 0));	
            #     println("reportOnEntities(context, facesToKeep,1,0): "                     ~ "\n" ~ reportOnEntities(context, facesToKeep,                  1, 0));	
            #     println("reportOnEntities(context, newEntitiesFromDeleteFace,0,0): "       ~ "\n" ~ reportOnEntities(context, newEntitiesFromDeleteFace,    1, 0));	
            #     println("reportOnEntities(context, clippedSheetBodiesInGalleySpace, 1, 0): "      ~ "\n" ~ reportOnEntities(context, clippedSheetBodiesInGalleySpace,     1, 0)); 
            #     # //debug(context,clippedSheetBodiesInGalleySpace);
            #     # //debug(context,sheetBodiesInGalleySpace);
            
            # # //delete the original sheetBodiesInGalleySpace, and set sheetBodiesInGalleySpace = clippedSheetBodiesInGalleySpace
            # opDeleteBodies(context, uniqueId(context, id),{entities: sheetBodiesInGalleySpace});
            # sheetBodiesInGalleySpace = clippedSheetBodiesInGalleySpace;

        # //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
        return sheetBodiesInGalleySpace

    def buildSheetBodiesInWorld(self):
        """ transforms sheetBodiesInGalleySpace according to self.transform (which says where to put the anchor point in world space) and
        self.anchor (which describes where the anchor point is in galley space). """
        sheetBodiesInWorld = qNothing()
        
        
        # //anchorPointInGalleySpace is the point in galley space that will be mapped to the origin of worldPlane.
        # // compute anchorPointInGalleySpace. 
        if is3dLengthVector(self.anchor):
            anchorPointInGalleySpace =  self.anchor;
        else:          
            # //compute scaledAnchorPoint, one way or another.
            if (isUnitlessVector(self.anchor) && size(self.anchor) >= 2):
                scaledAnchorPoint = resize(self.anchor, 3, 0); #//doing this resize lets us take an anchor that only gives x and y coordinates
            elif(self.anchor is galleyAnchor_e):
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
            else:
                throw ("anchor was neither a 3dLengthVector, nor a unitless vector containing at least two elements, nor a galleyAnchor_e enum value.");    
                
            # //at this point, scaledAnchorPoint is computed, so we can proceed to compute anchorPointInGalleySpace
            anchorPointInGalleySpace = elementWiseProduct(scaledAnchorPoint, vector(self.width, self.height, zeroLength));
        
        # //println("anchorPointInGalleySpace: " ~ toString(anchorPointInGalleySpace));		// anchorPointInGalleySpace
        
        
        sheetBodiesInGalleySpace = self.buildSheetBodiesInGalleySpace(context, uniqueId(context, id));
        # //println("reportOnEntities(context,sheetBodiesInGalleySpace,0): " ~ toString(reportOnEntities(context,sheetBodiesInGalleySpace,0)));
        # //debug(context, sheetBodiesInGalleySpace);
        opTransform(
            context, 
            uniqueId(context, id), 
            {
                "bodies": sheetBodiesInGalleySpace,
                "transform": transform(XY_PLANE, self.worldPlane) * transform(-anchorPointInGalleySpace)
            }
        )
        sheetBodiesInWorld = sheetBodiesInGalleySpace
        # //debug(context, sheetBodiesInWorld);
        # //println("reportOnEntities(context,sheetBodiesInWorld,0,0): " ~ toString(reportOnEntities(context,sheetBodiesInWorld,0,0)));		// reportOnEntities(context,sheetBodiesInWorld,0,0);
        return sheetBodiesInWorld

class TextRow:
    def __init__(self,
        owningGalley : Optional[Galley] = None,
        text : str = "",
        fontName : str = "Tinos-Italic.ttf",
        height = 1 * inch,
        basePoint = vector(0,0,0) * meter 
    ):
    


        self.height = height 
        # 1 * inch #//isLength ///when we go to create sheet bodies on the
        # galley, we will look at this value and scale the size of the bodies
        # accordingly.  We will scale the size of the bodies so that the nominal
        # height of the text (as would be measured from the
        # automatically-gnerated cotruction line segmens that an OnShape
        # sketchText sketch entity generates.) will become self.fontHeight.
        
        
        self.basePoint = basePoint # vector(0,0,0) * meter 
        #; //is3dLengthVector  //this is a vector, in galleySpace (galleySpace
        #is 3 dimensional, although only the x and y dimensions are significant
        #for the final results. (When we are building bodies for a layout, we
        #first create all the bodies "in galleySpace" and then transform them
        #all by the galleyToWorld transform.  
        
        # // The following comment was written before I decided to use the name
        # "galley".  Prior to 'galley', I was unsing the word "textLayout" to
        # refer to galley. //  (The 'paper' here is not to be confused with the
        # 'paper' on which a 2d drawing of this 3d model might be drawn).  (I
        # really need to come up with a better word than 'paper' for the current
        # project, because "paper" is already used in the context of making 2d
        # drawings.  Perhaps poster is a better word.  Broadside, banner,
        # billboard, marquee, signboard, foil. lamina, saran wrap, plastic wrap,
        # cling wrap, film, membrane, stratum, veneer, mat, varnish, skin,
        # graphicSkin, veil, screen, facade, parchment, velum, fabric, leaf,
        # inkMembrane, inkSpace, inkSheet, inkScape, placard, plaque, plate,
        # proofPlate, blackboard, whiteboard, readerboard, engraving, galley (in
        # the context of a printing press) - a galley is the tray into which a
        # person would lay type (e.g. lead (Pb) type - think 'printing press')
        # into and tighten the type into place.  This is exactly the notion I am
        # after, and "galley" does not have any alternate uses in the context of
        # 3d geomtric modeling.  The galley isn't really an solid object within
        # the model - it is a tool that can be brought to bear on the model to
        # make engraves in the solid of the model (or embosses - yes, that
        # stretches the analogy a bit, but the concept is close enough), and
        # then, when you are finished with the galley, you put it back in the
        # drawer from whence it came.  In other words, the galley itself is not
        # part of the final finsihed model, but the marks that the galley makes
        # are part of the finished model.
        
        
        
        self._text = text #"" #; //this value can (and probably will be) changed later by the calling code (via self.set()).
        self._fontName = fontName #"Tinos-Italic.ttf" #; //this value can (and probably will be) changed later by the calling code (via self.set()).
        self._owningGalley : Optional[Galley] = owningGalley  #  //this will be set to a galley object when the time comes to add this textRow to a particular owning textLayout. 
        
        # self._scaleFreeShapeParameters = ["scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"] #; //'depth' here is in the TeX sense of the word (depth is the amount by which the characeters protrude below the baseline)
        # // the members of scaleFreeShape are numbers with length units, but any one of these values is not significnt in itself -- what matters is the ratio between 
        # // and among pairs of 'scaleFree' dimensions.  These ratios describe the shape of the textRow irrespective of scale.
        

        # self._shapeChangers = ["text", "fontName"];
        # # // these are the names of properties of private[], which will, when changed, affect the scaleFreeShapeParameters.  We will allow the user to set these properties (via a setter function), 
        # # // but the setter function will turn on the shapeIsDirty flag so that we will know that we need to recompute the shape if we want good shape data.
        
        
        self._shapeIsDirty = True
        # # //this is a flag that we will set to true whenever any of the parameters designated in shapeChangers is set.
        
        
        # self._getablePrivates = ["text", "fontName", "owningGalley", "scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"]; #//"width" is computed on demand from the scaleFreeShape and the fontHeight, which is the one parameter that 
        # # //whenever the calling code uses self.set() to set a private member, if the name of the private member is in self._shapeChangers, we recompute the scaleFreeShapeParameters
        
        self._scaleFreeHeight = zeroLength
        self._scaleFreeWidth = zeroLength
        self._scaleFreeDepth = zeroLength

    
    def _computeShape(self):
        self._buildScaleFreeSheetBodies(newContextWithDefaults(), makeId("dummyDummyDummy"))
        # //  As a side effect, self._buildScaleFreeSheetBodies() computes and sets the scale free shape parameters, so 
        # we merely have to let it run in a temporary dummy context.  We don't care about saving the results of the 
        # build in the temporary context, we are just getting the data we need and then letting the temporary 
        # context be destroyed by garbage collection. 

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
                        "text": self.text,
                        "fontName": self.fontName,
                    }
                );
            # //println("textIdMap: " ~ textIdMap);
        } catch(error) {
            println("skText threw an excpetion.");   
        }
        try{skSolve(workingSketch);}
        # //debug(context, qConstructionFilter(qCreatedBy(idOfWorkingSketch, EntityType.EDGE), ConstructionObject.YES));
        var mySketchTextData;
        try{mySketchTextData = getSketchTextData(context, idOfWorkingSketch, sketchEntityIdOfSketchText);}
        try{self._scaleFreeHeight = mySketchTextData.nominalHeight;}
        try{self._scaleFreeWidth = mySketchTextData.nominalWidth;}
        
        //println("mySketchTextData: " ~ mapToString(mySketchTextData));
        
        var idOfBodyCopy = id + "bodyCopy";
        
        # //opPattern creates copies of the specified bodies.
        # // we want to create a copy of the sheetBodies in the sketch, so that we have a copy, which is independent of the original sketch, so that we can then delete the sketch and be left with just the faces.
        
        # //qSketchRegion returns all faces of all sheetBodies in the sketch if the second argument (filterInnerLoops) is false, or else the all the 'outer' faces of all sheetBodies in the sketch if filterInnerLoops is true.
        var inkSheets is Query = qBodyType( qEntityFilter( qOwnerBody(qSketchRegion(idOfWorkingSketch,false)), EntityType.BODY), BodyType.SHEET) ;  //I realize that some of these filters are probably redundant - I just want to be darn sure that I am picking out exactly what I want (namely all sheetBodies in the sketch) and nothing else.
        
        # //delete all the even-rank faces (this concept of ranking of faces of a planar sheetBody is my own terminology -- not from the OnShape documentation.)
        deleteEvenRankFaces(context, id + "deleteEvenRankFaces", inkSheets);
        
        # //To DO: use onshape ev... evaluation functions to find the actual bounding box of the glyphs.
        
        
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
        
        
        # //print(reportOnEntities(context, inkSheets,0,0));
        # //debug(context, inkSheets);
        # //debug(context, qCreatedBy(idOfBodyCopy));
        
        # //debug(context, qCreatedBy(idOfWorkingSketch));
        
        # //get rid of all the entities in the sketch, which we do not need now that we have extracted the sheetBodies that we care about.
        try silent{opDeleteBodies(
            context,
            uniqueId(context, id),
            {entities:qCreatedBy(idOfWorkingSketch)}
        );  } 
        
        
        self._shapeIsDirty = false;
        # //debug(context, qCreatedBy(idOfWorkingSketch));
        return scaleFreeSheetBodies;

    # // builds the sheetBodies in galley space, returns the resulting sheetBodies
    def buildSheetBodiesInGalleySpace(self, context is Context, id is Id):
        var scaleFreeSheetBodies = self._buildScaleFreeSheetBodies(context, id + "buildScaleFreeSheetBodies");
        # //scale and translate and scaleFreeSheetBodies according to self.get("height") and self.get("basePoint")
        
        var idOfTransformOperation = "scaleFreeTextRowToGalley";

        try{
            opTransform(context, id + idOfTransformOperation,
                {
                    "bodies": scaleFreeSheetBodies,
                    "transform": transform(self.basePoint) * scaleUniformly(self.height/self.scaleFreeHeight)    
                }
            );
        }
        
        
        return scaleFreeSheetBodies;  // I am assuming the the query for the bodies still refers the (now transformed bodies).

    def ensureThatComputedShapeIsUpToDate(self):
        # //recompute the shape if the shape data is out of date ( self._computeShape() will clear the shapeIsDirty flag.)
        if self._shapeIsDirty:
            self._computeShape()
    
    # for(var propertyName in self._getablePrivates)
    # {
    #     if(isIn(propertyName, self._scaleFreeShapeParameters))
    #     {
    #         this[]["get_" ~ propertyName] = 
    #         function(){
    #             self.ensureThatComputedShapeIsUpToDate()
    #             return private[][propertyName];
    #         };   
    #     } else
    #     {
    #         this[]["get_" ~ propertyName] = function(){return private[][propertyName];};   
    #     }
    # }

    # self._shapeChangers = ["text", "fontName"];
    # // these are the names of properties of private[], which will, when changed, affect the scaleFreeShapeParameters.  We will allow the user to set these properties (via a setter function), 
    # // but the setter function will turn on the shapeIsDirty flag so that we will know that we need to recompute the shape if we want good shape data.
 

    # We will allow the user to set these properties (via a setter function), 
    # // but the setter function will turn on the shapeIsDirty flag so that we will know that we need to recompute the shape if we want good shape data.
    #=== PROPERTIES THAT AFFECT SHAPE: ===
    @property
    def text(self): return self._text
    
    @text.setter
    def text(self, newText):
        self._text = newText
        self._shapeIsDirty = True

    @property
    def fontName(self): return self._fontName
    
    @fontName.setter
    def fontName(self, newFontName):
        self._fontName = newFontName
        self._shapeIsDirty = True
    #=== END PROPERTIES THAT AFFECT SHAPE ===
 

    # ["text", "fontName", "scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"]; #//"width" is computed on demand from the scaleFreeShape and the fontHeight, which is the one parameter that 
    # //whenever the calling code uses self.set() to set a private member, if the name of the private member is in self._shapeChangers, we recompute the scaleFreeShapeParameters
    
    #=== PROPERTIES THAT CONSTITUTE THE SCALE-FREE SHAPE: ===
    # self._scaleFreeShapeParameters = ["scaleFreeHeight", "scaleFreeWidth", "scaleFreeDepth"] #; //'depth' here is in the TeX sense of the word (depth is the amount by which the characeters protrude below the baseline)
    # // the members of scaleFreeShape are nuumbers with length units, but any one of these values is not significnt in itself -- what matters is the ratio between 
    # // and among pairs of 'scaleFree' dimensions.  These ratios describe the shape of the textRow irrespective of scale.

    @property
    def scaleFreeHeight(self):
        self.ensureThatComputedShapeIsUpToDate()
        return self._scaleFreeHeight
    
    @property
    def scaleFreeWidth(self):
        self.ensureThatComputedShapeIsUpToDate()
        return self._scaleFreeWidth
    
    @property
    def scaleFreeDepth(self):
        self.ensureThatComputedShapeIsUpToDate()
        return self._scaleFreeDepth

    #=== END PROPERTIES THAT CONSTITUTE THE SCALE-FREE SHAPE: ===
    
    @property
    def width(self):
        return self.height * self.scaleFreeWidth/self.scaleFreeHeight

    
    
    # for(var propertyName in self._shapeChangers)
    # {
    #     this[]["set_" ~ propertyName] = 
    #         function(newValue)
    #         {
    #             private[][propertyName] = newValue;
    #             self._shapeIsDirty = true;
    #             return newValue;
    #         };
    # }
    
