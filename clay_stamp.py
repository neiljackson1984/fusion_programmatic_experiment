import adsk.core, adsk.fusion, traceback
from typing import Any, Dict, Optional, Sequence, Union
from .braids.fscad.src.fscad import fscad as fscad
import traceback
import pathlib
import pprint
import json

from .utility import *

def makeClayStamp(
    # parameters controlling the svg import process:                                           
    pathOfSvgFile                             : str                                 ,
    pathOfOutputFile                          : str                                 ,
    svgNativeLengthUnit                       : float                               ,
    translateAsNeededInOrderToPlaceMidPoint   : bool                                ,
                                                                                                                          
    #parameters controlling the stamp sans handle:                                                    
    rootAngularSpan                           : float                               ,    #         = 120 * degree,
    letterRadialExtent                        : float                               ,    #         = 1/4 * inch,
    plinthRadialExtent                        : float                               ,    #         = 1/4 * inch,
    letterDraftAngle                          : float                               ,    #         = - 4 *degree,
    plinthDraftAngle                          : float                               ,    #         = - 7 *degree,
    offsetCornerType                          : adsk.fusion.OffsetCornerTypes       ,    #              =  
    doMultipleLoftSegments                    : bool                                ,    #                  ,
    maximumAllowedRadialExtentOfLoftSegment   : float                               ,    #            ,
                                                                                                                           
    #parameters controlling the handle:                                                            
    handlePathExtentZ                         : float                               ,    #    =  25 * millimeter,
    handlePathExtentY                         : float                               ,    #    =  40 * millimeter,
    handlePathRoundingRadius                  : float                               ,    #    =  10 * millimeter,
    handleProfileExtentX                      : float                               ,    #    =  15 * millimeter,
    handleProfileExtentY                      : float                               ,    #    =  6  * millimeter,
    handleProfileRoundingRadius               : float                               ,    #    =  2  * millimeter,
    handleToPlinthFilletRadius                : float                               ,    #    =  6  * millimeter,
    flatBackFillThickness                     : float                               ,    #    =  3  * millimeter
) -> None:
    # pathOfSvgFile = pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg')
    # pathOfSVGFile = pathlib.Path(__file__).parent.joinpath('test_logo1.svg')

    # parameterReportPrettyPrinter = pprint.PrettyPrinter(    )

    metadata = {
        'parameters': json.loads(json.dumps(locals()))
    }
    metadataReport : str = json.dumps(metadata, indent=4)
    # print(f"metadataReport: {metadataReport}")

    transformUponImport = castToMatrix3D(castToNDArray( rotation(angle=90*degree) ))
    # this is a bit of a hack to account for the fact that I have not made the
    # cylindrical wrapping totally general with respect to orientation of the
    # cylinder; at the moment, the cylinder orientation, and map from xy plane
    # to parametric space of cylinder is hard-coded.

    sheetBodiesGroupedByRank = getSheetBodiesGroupedByRankFromSvg(
        pathOfSvgFile = pathOfSvgFile, 
        svgNativeLengthUnit = svgNativeLengthUnit, 
        translateAsNeededInOrderToPlaceMidPoint = translateAsNeededInOrderToPlaceMidPoint,
        desiredMidpointDestination = (0,0,0), 
        transform = transformUponImport
    )

    # we want to obtain two (sets of) flat sheet bodies:
    # 1.  The plinth footprint (which I am calling the 'support' (not to be
    #     confused with 'support' in the context of 3d printing)
    # 2.  The embossed design.

    supportSheetBodies : Sequence[adsk.fusion.BRepBody] = tuple(
        deleteInnerLoops(rankZeroSheetBody)
        for rankZeroSheetBody in sheetBodiesGroupedByRank[0]
    )

    oddRankSheetBodies = tuple(
        sheetBody
        for r in range(len(sheetBodiesGroupedByRank))
        for sheetBody in sheetBodiesGroupedByRank[r]
        if r % 2 == 1
    )

    minisculeEdgeLengthThreshold = 0.01 * millimeter
    numberOfShortEdgeCandidatesToHighlight = 3
    edge : adsk.fusion.BRepEdge
    edgesSortedByLength = sorted(
        (
            edge
            for sheetBody in (*supportSheetBodies, *oddRankSheetBodies)
            for edge in sheetBody.edges
        ),
        key=getLengthOfEdge
    )

    for edge in edgesSortedByLength:
        length = getLengthOfEdge(edge)
        if length < minisculeEdgeLengthThreshold:
            highlight(
                edge,
                **makeHighlightParams(f"miniscule edge of length {length}", show=False)
            )

    for i in range(min(numberOfShortEdgeCandidatesToHighlight, len(edgesSortedByLength))):
        highlight(
            edgesSortedByLength[i],
            **makeHighlightParams(f"short edge candidate {i}, length {getLengthOfEdge(edgesSortedByLength[i])}", show=False)
        )
    fscad.BRepComponent(*supportSheetBodies, name=f"supportSheetBodies").create_occurrence()
    fscad.BRepComponent(*oddRankSheetBodies, name=f"oddRankSheetBodies").create_occurrence()
            

    supportFscadComponent = fscad.BRepComponent(*supportSheetBodies, name=f"support"); 
    print(f"supportFscadComponent.mid: {(supportFscadComponent.mid().x, supportFscadComponent.mid().y, supportFscadComponent.mid().z)}")
    print(f"supportFscadComponent.extent x: {(supportFscadComponent.max().x - supportFscadComponent.min().x)}")
    print(f"supportFscadComponent.extent y: {(supportFscadComponent.max().y - supportFscadComponent.min().y)}")
    
    # supportFscadComponent.create_occurrence()
    # oddRankFscadComponent = fscad.BRepComponent(*oddRankSheetBodies, name=f"odd rank"); oddRankFscadComponent.create_occurrence()
    # rankZeroFscadComponent = fscad.BRepComponent(*rankZeroSheetBodies, name=f"rank zero"); rankZeroFscadComponent.create_occurrence()

    rootRadius = ( supportFscadComponent.max().y - supportFscadComponent.min().y ) * radian / rootAngularSpan

    print(f"rootRadius: {rootRadius}")
    # rootRadius = 3*centimeter
    letterRadiusMax = rootRadius
    letterRadiusMin = letterRadiusMax - letterRadialExtent
    plinthRadiusMax = letterRadiusMin
    plinthRadiusMin = plinthRadiusMax - plinthRadialExtent
    cylinderOrigin = (0,0,rootRadius)       
    cylinderAxisDirection = xHat

    # these argument values will be splatted into all calls to
    # wrapSheetBodiesAroundCylinder() .
    commonWrappingArguments = {
        'cylinderOrigin'                            : cylinderOrigin ,
        'cylinderAxisDirection'                     : cylinderAxisDirection ,
        'rootRadius'                                : rootRadius ,
        'offsetCornerType'                          : offsetCornerType,
        'doMultipleLoftSegments'                    : doMultipleLoftSegments,
        'maximumAllowedRadialExtentOfLoftSegment'   : maximumAllowedRadialExtentOfLoftSegment
    }

    #These are the sheets that, along with rootRadius define the shapes in
    # (length, angle) space: (We are not doing the circumferential
    # stretching to account for differing radii here)-- that gets done by
    # wrapSheetBodiesAroundCylinder() (by using both the rootRadius and the
    # wrappingRadius parameters).

    # letterSheetsAtMaxRadius = oddRankSheetBodies
    # plinthSheetsAtMaxRadius = supportSheetBodies
    # plinthSheetsAtMinRadius = offsetSheetBodies(plinthSheetsAtMaxRadius, math.tan(plinthDraftAngle)* (plinthRadiusMax - plinthRadiusMin))
    # plinthSheetsAtMinRadiusFscadComponent = fscad.BRepComponent(*plinthSheetsAtMinRadius, name=f"plinthSheetsAtMinRadius"); plinthSheetsAtMinRadiusFscadComponent.create_occurrence()

    # letterSheetsAtMinRadius = offsetSheetBodies(letterSheetsAtMaxRadius, math.tan(letterDraftAngle) * (letterRadiusMax - letterRadiusMin))
    # letterSheetsAtMinRadiusFscadComponent = fscad.BRepComponent(*letterSheetsAtMinRadius, name=f"letterSheetsAtMinRadius"); letterSheetsAtMinRadiusFscadComponent.create_occurrence()

    highlight(
        # tuple(destinationSurface.evaluator.getIsoCurve(0,isUDirection=False)),
        adsk.core.Circle3D.createByCenter(
            center = castToPoint3D(cylinderOrigin),
            normal = castToVector3D(cylinderAxisDirection),
            radius = rootRadius
        ),
        **makeHighlightParams("cylinder preview", show=False)
    )


    edifiedPlinthBodies = extrudeDraftAndWrapSheetbodiesAroundCylinder(
        sheetBodies = supportSheetBodies,
        wrappingRadiusStart = plinthRadiusMax,
        wrappingRadiusEnd = plinthRadiusMin,
        draftAngle = plinthDraftAngle ,
        doFlatBackFill = True ,
        flatBackFillThickness = flatBackFillThickness,
        **commonWrappingArguments
    )

    edifiedPlinthBodiesFscadComponent = fscad.BRepComponent(*edifiedPlinthBodies, name=f"edifiedPlinthBodies")

    handlePath = [
        adsk.core.Line3D.create(
            adsk.core.Point3D.create(   0,  -handlePathExtentY/2,  edifiedPlinthBodiesFscadComponent.max().z ) , 
            adsk.core.Point3D.create(   0,  -handlePathExtentY/2,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ - handlePathRoundingRadius ) , 
        ),
        adsk.core.Arc3D.createByCenter(
            center=adsk.core.Point3D.create(0 , -handlePathExtentY/2 + handlePathRoundingRadius,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ - handlePathRoundingRadius),
            normal=castToVector3D(-xHat),
            referenceVector=castToVector3D(-yHat),
            radius = handlePathRoundingRadius,
            startAngle=0,
            endAngle=90*degree
        ),
        adsk.core.Line3D.create(
            adsk.core.Point3D.create(   0,  -handlePathExtentY/2 + handlePathRoundingRadius,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ ) , 
            adsk.core.Point3D.create(   0,  +handlePathExtentY/2 - handlePathRoundingRadius,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ ) , 
        ),
        adsk.core.Arc3D.createByCenter(
            center=adsk.core.Point3D.create(0 , +handlePathExtentY/2 - handlePathRoundingRadius,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ - handlePathRoundingRadius),
            normal=castToVector3D(-xHat),
            referenceVector=castToVector3D(zHat),
            radius = handlePathRoundingRadius,
            startAngle=0,
            endAngle=90*degree
        ),
        adsk.core.Line3D.create(
            adsk.core.Point3D.create(   0,  +handlePathExtentY/2,  edifiedPlinthBodiesFscadComponent.max().z + handlePathExtentZ - handlePathRoundingRadius ) , 
            adsk.core.Point3D.create(   0,  +handlePathExtentY/2,  edifiedPlinthBodiesFscadComponent.max().z ) , 
        )
    ]

    handleProfileFscadComponent = fscad.BRepComponent(
        roundedRect(
            extentX=handleProfileExtentX,
            extentY=handleProfileExtentY,
            roundingRadius=handleProfileRoundingRadius
        ),
        name='handleProfile'
    ).translate(0,  -handlePathExtentY/2, edifiedPlinthBodiesFscadComponent.max().z)
    
    # handleProfileFscadComponent.create_occurrence()
    # highlight(handlePath, **makeHighlightParams("handlePath", show=False))

    handleFscadComponent = fscad.Sweep(handleProfileFscadComponent, path=handlePath, name='handle')
    # handleFscadComponent.create_occurrence()

    edifiedLetterBodies = extrudeDraftAndWrapSheetbodiesAroundCylinder(
        sheetBodies = oddRankSheetBodies,
        wrappingRadiusStart = letterRadiusMax,
        wrappingRadiusEnd = letterRadiusMin,
        draftAngle = letterDraftAngle ,
        **commonWrappingArguments
    )

    plinthOccurence=edifiedPlinthBodiesFscadComponent.create_occurrence()
    handleToolOccurence=handleFscadComponent.create_occurrence()
    initialEntityTokensOfPlinth = captureEntityTokens(plinthOccurence)
    combineFeatureInput = rootComponent().features.combineFeatures.createInput(targetBody=plinthOccurence.bRepBodies.item(0), toolBodies=fscad._collection_of(handleToolOccurence.bRepBodies))
    combineFeatureInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    combineFeature = rootComponent().features.combineFeatures.add(combineFeatureInput)
    handleToolOccurence.deleteMe()
    edgesDescendedFromInitialEdges = [
        entity 
        for item in initialEntityTokensOfPlinth['bodies']
        for initialEdgeEntityToken in item['edges']
        for entity in design().findEntityByToken(initialEdgeEntityToken)
    ]

    facesDescendedFromInitialFaces = [
        entity 
        for item in initialEntityTokensOfPlinth['bodies']
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
    # highlight(edgesOfInterest, **makeHighlightParams("edgesOfInterest", show=False))
    

    # filletFeatureInput = plinthOccurence.component.features.filletFeatures.createInput()
    # filletFeatureInput.addConstantRadiusEdgeSet(
    #     edges= fscad._collection_of(edgesOfInterest),
    #     radius= adsk.core.ValueInput.createByReal(handleToPlinthFilletRadius),
    #     isTangentChain=False
    # )
    # filletFeature = plinthOccurence.component.features.filletFeatures.add(filletFeatureInput)

    chamferFeatureInput = plinthOccurence.component.features.chamferFeatures.createInput2()
    chamferFeatureInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges=fscad._collection_of(edgesOfInterest),
        isTangentChain=False,
        distance=adsk.core.ValueInput.createByReal(handleToPlinthFilletRadius)
    )
    chamferFeature = plinthOccurence.component.features.chamferFeatures.add(chamferFeatureInput)
    
    
    mainFscadComponent = fscad.Union(fscad.BRepComponent(*plinthOccurence.component.bRepBodies, *edifiedLetterBodies),name='main')
    plinthOccurence.deleteMe()

    mainFscadOccurrence = mainFscadComponent.create_occurrence()
    workingComponent = mainFscadOccurrence.component


    writeMetadataReportToSketchText = True
    if writeMetadataReportToSketchText:
        #write metadataReport into sketchText:
        occurrenceOfComponentToContainTheMetadataReport = workingComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        componentToContainTheMetadataReport = occurrenceOfComponentToContainTheMetadataReport.component
        componentToContainTheMetadataReport.name = "metadata_report"
        occurrenceOfComponentToContainTheMetadataReport.isLightBulbOn = False
        sketch : Optional[adsk.fusion.Sketch] = componentToContainTheMetadataReport.sketches.add(componentToContainTheMetadataReport.xYConstructionPlane); assert sketch is not None
        sketch.name = "metadata_report"
        sketch.isLightBulbOn = True
        sketchTextInput = sketch.sketchTexts.createInput2(formattedText=metadataReport, height = 4 * millimeter)
        sketchTextInput.fontName = "Consolas"
        result = sketchTextInput.setAsMultiLine(
            cornerPoint = adsk.core.Point3D.create(0,0,0),
            diagonalPoint = adsk.core.Point3D.create(1000 * millimeter, -0.1 * millimeter, 0),
            horizontalAlignment = adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
            verticalAlignment = adsk.core.VerticalAlignments.TopVerticalAlignment,
            characterSpacing=0.0
        ); assert result
        metadataReportSketchText = sketch.sketchTexts.add(sketchTextInput); assert metadataReportSketchText is not None
        
 

    writeMetadataReportToCustomGraphics = False
    if writeMetadataReportToCustomGraphics:
        #unfortunately, custome grpahics do not seem to persist when the file is saved, and are therefore useless for our purpose here.
        #write metadataReport into customGraphics container within a child component (to be able to toggle off and on in the ui):
        occurrenceOfComponentToContainTheMetadataReport = workingComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        componentToContainTheMetadataReport = occurrenceOfComponentToContainTheMetadataReport.component
        componentToContainTheMetadataReport.name = "metadata_report"
        occurrenceOfComponentToContainTheMetadataReport.isLightBulbOn = True
        customGraphicsGroupToContainTheCustomGraphics = componentToContainTheMetadataReport.customGraphicsGroups.add()
        customGraphicsText = customGraphicsGroupToContainTheCustomGraphics.addText(
            formattedText=metadataReport,
            font="Consolas",
            size=15,
            transform= adsk.core.Matrix3D.create()
        )
        
        # customGraphicsText.transform = translation((0,300,0))

        customGraphicsText.billBoarding = adsk.fusion.CustomGraphicsBillBoard.create(anchorPoint=adsk.core.Point3D.create(0,0,0))
        # customGraphicsText.billBoarding = None
        customGraphicsText.viewPlacement = adsk.fusion.CustomGraphicsViewPlacement.create(
            anchorPoint=adsk.core.Point3D.create(0,0,0),
            viewCorner= adsk.fusion.ViewCorners.lowerRightViewCorner,
            viewPoint=adsk.core.Point2D.create(customGraphicsText.width+20,customGraphicsText.height+20)
        )
        customGraphicsText.viewScale = adsk.fusion.CustomGraphicsViewScale.create(
            pixelScale=1,
            anchorPoint=adsk.core.Point3D.create(0,0,0)
        )
        customGraphicsText.isSelectable = False



    result = design().exportManager.execute(
        design().exportManager.createFusionArchiveExportOptions(
            pathlib.Path(pathOfOutputFile).resolve().as_posix(),
            workingComponent
        )
    ); assert result


    # result = design().exportManager.execute(
    #     design().exportManager.createSTEPExportOptions(
    #         pathlib.Path(pathOfOutputFile).with_suffix('.step').resolve().as_posix(),
    #         workingComponent
    #     )
    # ); assert result

    # result = design().exportManager.execute(
    #     design().exportManager.createIGESExportOptions(
    #         pathlib.Path(pathOfOutputFile).with_suffix('.iges').resolve().as_posix(),
    #         workingComponent
    #     )
    # ); assert result
    # fscad.BRepComponent(*edifiedLetterBodies, name=f"edifiedLetterBodies").create_occurrence()













#====================================


        # def reportOnPlanarSurface(arg :  Union[ adsk.core.Surface, adsk.fusion.BRepFace], title : str) -> None:
            
        #     plane : adsk.core.Plane
        #     surfaceEvaluator : adsk.core.SurfaceEvaluator
        #     if isinstance(arg, adsk.core.Surface):
        #         plane = arg
        #         surfaceEvaluator = plane.evaluator
        #     elif isinstance(arg, adsk.fusion.BRepFace):
        #         plane = arg.geometry
        #         surfaceEvaluator = arg.evaluator
        #     else:
        #         assert False

        #     assert isinstance(plane, adsk.core.Plane)


        #     originPoint3D = adsk.core.Point3D.create(0,0,0)
        #     xRefPoint3D   = adsk.core.Point3D.create(1,0,0)
        #     yRefPoint3D   = adsk.core.Point3D.create(0,1,0)

        #     originPoint2D = adsk.core.Point2D.create(0,0)
        #     xRefPoint2D   = adsk.core.Point2D.create(1,0)
        #     yRefPoint2D   = adsk.core.Point2D.create(0,1)
            
        #     print(f"{title}")

        #     result, originPoint3DPrime = surfaceEvaluator.getParameterAtPoint(originPoint3D); 
        #     print(f"    originPoint3DPrime: " + str(castToNDArray(originPoint3DPrime) if result else "failed") )
            
        #     result, xRefPoint3DPrime = surfaceEvaluator.getParameterAtPoint(xRefPoint3D); assert result
        #     print(f"    xRefPoint3DPrime: " + str(castToNDArray(xRefPoint3DPrime) if result else "failed") )

        #     result, yRefPoint3DPrime = surfaceEvaluator.getParameterAtPoint(yRefPoint3D); assert result
        #     print(f"    yRefPoint3DPrime: " + str(castToNDArray(yRefPoint3DPrime) if result else "failed") )
            
        #     print("")

        #     result, originPoint2DPrime = surfaceEvaluator.getPointAtParameter(originPoint2D); assert result
        #     print(f"    originPoint2DPrime: " + str(castToNDArray(originPoint2DPrime) if result else "failed") )

        #     result, xRefPoint2DPrime = surfaceEvaluator.getPointAtParameter(xRefPoint2D); assert result
        #     print(f"    xRefPoint2DPrime: " + str(castToNDArray(xRefPoint2DPrime) if result else "failed") )

        #     result, yRefPoint2DPrime = surfaceEvaluator.getPointAtParameter(yRefPoint2D); assert result
        #     print(f"    yRefPoint2DPrime: " + str(castToNDArray(yRefPoint2DPrime) if result else "failed") )
            
        #     print("")
            
        #     print(f"    plane.origin     : {castToNDArray(plane.origin)}")
        #     print(f"    plane.uDirection : {castToNDArray(plane.uDirection)}")
        #     print(f"    plane.vDirection : {castToNDArray(plane.vDirection)}")
        #     print(f"    plane.normal     : {castToNDArray(plane.normal)}")

        #     pToM = planeParameterSpaceToModelSpaceTransform(arg)
        #     print(f"    pToM: \n{castToNDArray(pToM)}")
        #     print(f"    castToMatrix2D(pToM): \n{castToNDArray(castToMatrix2D(pToM))}")

        #     pRange : adsk.core.BoundingBox2D = surfaceEvaluator.parametricRange()
        #     if pRange is None:
        #         print("    pRange is None." )
        #     else:
        #         minParameterPoint = castTo4dArray(pRange.minPoint)
        #         maxParameterPoint = castTo4dArray(pRange.maxPoint)
        #         parameterSpan = maxParameterPoint - minParameterPoint
        #         parameterAspectRatio = parameterSpan[0]/parameterSpan[1]

        #         result, value = surfaceEvaluator.getPointAtParameter(pRange.minPoint); assert result
        #         minParameterPointPrime = castTo4dArray(value)

        #         result, value = surfaceEvaluator.getPointAtParameter(pRange.maxPoint); assert result
        #         maxParameterPointPrime = castTo4dArray(value)
        #         primedParameterSpan = maxParameterPointPrime - minParameterPointPrime
        #         primedAspectRatio = primedParameterSpan[0]/primedParameterSpan[1]

        #         # confirm that surfaceEvaluator.getPointAtParameter() is doing essentially the same thing as pToM (ignoring all the thrashiung about with types)

        #         pToMBadnessForMinPoint = norm(
        #             castTo4dArray(surfaceEvaluator.getPointAtParameter(pRange.minPoint)[1])  
        #             - 
        #             castToNDArray(pToM) @  castTo4dArray(pRange.minPoint)
        #         )
        #         pToMBadnessForMaxPoint = norm(
        #             castTo4dArray(surfaceEvaluator.getPointAtParameter(pRange.maxPoint)[1])  
        #             - 
        #             castToNDArray(pToM) @  castTo4dArray(pRange.maxPoint)
        #         )
        #         assert pToMBadnessForMaxPoint < 0.00001
        #         assert pToMBadnessForMinPoint < 0.00001
                

        #         uRange = (pRange.minPoint.x, pRange.maxPoint.x)
        #         vRange = (pRange.minPoint.y, pRange.maxPoint.y)
        #         uSpan =  uRange[1] - uRange[0]
        #         vSpan =  vRange[1] - vRange[0]
        #         aspectRatioInParameterSpace = uSpan/vSpan

        #         print(f"    minParameterPoint           : {minParameterPoint}"           )
        #         print(f"    maxParameterPoint           : {maxParameterPoint}"           )
        #         print(f"    parameterSpan               : {parameterSpan}"               )
        #         print(f"    parameterAspectRatio        : {parameterAspectRatio}"        )

        #         print("")
        #         print("")
        #         print(f"    castTo4dArray(pRange.minPoint)      : {castTo4dArray(pRange.minPoint)}")

        #         print(f"    minParameterPointPrime      : {minParameterPointPrime}  or  {castToNDArray(pToM) @  castTo4dArray(pRange.minPoint)} "      )
        #         print(f"    maxParameterPointPrime      : {maxParameterPointPrime}  or  {castToNDArray(pToM) @  castTo4dArray(pRange.maxPoint)}"      )
        #         print(f"    primedParameterSpan         : {primedParameterSpan}"         )
        #         print(f"    primedAspectRatio           : {primedAspectRatio}"           )
        #         print(f"    pToMBadnessForMinPoint      : {pToMBadnessForMinPoint}"         )
        #         print(f"    pToMBadnessForMaxPoint      : {pToMBadnessForMaxPoint}"           )
                
        #         if not (pToMBadnessForMaxPoint < 0.00001 and pToMBadnessForMinPoint < 0.00001):
        #             print ("oops")



        #     print("")

        # xyPlane = adsk.core.Plane.create(origin=adsk.core.Point3D.create(0,0,0), normal=adsk.core.Vector3D.create(0,0,1) )
        # sampleFace = supportFscadComponent.faces[0].brep
        
        # tempBody : adsk.fusion.BRepBody = temporarayBrepManager().copy(sampleFace)
        # scalingTransform : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
        # scaleFactor = 1/3.7616
        # result = scalingTransform.setCell(0,0,scaleFactor); assert result
        # # result = scalingTransform.setCell(1,1,scaleFactor*2.825); assert result
        # result = scalingTransform.setCell(1,1,scaleFactor); assert result
        # result = scalingTransform.setCell(2,2,scaleFactor); assert result
        # print(f"scalingTransform: {castToNDArray(scalingTransform)}" )
        # scaledTempBody = temporarayBrepManager().copy(tempBody)
        # result = temporarayBrepManager().transform(scaledTempBody, scalingTransform); assert result
        # tempFace = tempBody.faces[0]
        # scaledTempFace = scaledTempBody.faces[0]
        
        # reportOnPlanarSurface(xyPlane                  , "xyPlane"                 )
        # # reportOnPlanarSurface(sampleFace               , "sampleFace"              )
        # # reportOnPlanarSurface(sampleFace.geometry      , "sampleFace.geometry"     )
        # # the face.geometry.evaluator is the same as face.evaluator with the exception that face.geometry.evaluator has .parametricRange() being None.
        # a : adsk.core.Plane = tempFace.geometry

        # b : adsk.core.Plane = tempFace.geometry

        # result = b.transformBy(scalingTransform); assert result

        
        # reportOnPlanarSurface(tempFace                 , "tempFace"                )
        # # reportOnPlanarSurface(tempFace.geometry        , "tempFace.geometry"       )
        # reportOnPlanarSurface(scaledTempFace           , "scaledTempFace"          )
        # reportOnPlanarSurface(scaledTempFace.geometry  , "scaledTempFace.geometry" )
        # # god damn it, face.evaluator and face.geometry.evaluator are not generally equivalent (do not do the same to parameter space to model space map).
        # reportOnPlanarSurface(b                        , "b"          )
        
        
        # regarding the parameterization of planar surfaces:
        # the "default" tenedency within Fusion is for parameter

        # fscad.BRepComponent(*oddRankSheetBodies, name=f"oddRankSheetBodies").create_occurrence()
        # fscad.BRepComponent(*supportSheetBodies, name=f"supportSheetBodies").create_occurrence()
        # getAllSheetBodiesFromSketch() (due to Fusion's underlying sketch region logic) gives
        # us a set of non-overlapping sheets.  We want to categorize these sheets by rank, so that 
        # we can say that the outer edge of the rank 0 sheets is the boundary of the plinth footprint,
        # and all sheets having ((rank >0) and (rank is odd)) are the "ink" sheets (the ink on the page).
        

