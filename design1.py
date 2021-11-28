import adsk.core, adsk.fusion, traceback
from typing import Any, Dict, Optional, Sequence, Union
from .braids.fscad.src.fscad import fscad as fscad
import traceback
import pathlib


from .utility import *


def run(context:dict):
 
    def design1() -> None:
        


        pathOfSVGFile = pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg')
        # pathOfSVGFile = pathlib.Path(__file__).parent.joinpath('test_logo1.svg')


        fileSpecificOptionalArgsForSVGProcessing = {
            'eXotic logo 1 2.svg': {
                'svgNativeLengthUnit': ((1/2 * inch)/36.068069458007805), 
                'translateAsNeededInOrderToPlaceMidPoint': (0,0,0),
                'transform': castToMatrix3D(
                        castToNDArray( rotation(angle=90*degree) )
                    )
            }
        }.get(pathOfSVGFile.name, {
            'translateAsNeededInOrderToPlaceMidPoint': (0,0,0),
            'transform': castToMatrix3D(
                    castToNDArray( rotation(angle=90*degree) )
                )
        }) 
        
        # test1(
        #     pathOfSVGFile, 
        #     **fileSpecificOptionalArgsForSVGProcessing
        # )

        



        sheetBodiesGroupedByRank = getSheetBodiesGroupedByRankFromSvg(
            pathOfSVGFile, 
            **fileSpecificOptionalArgsForSVGProcessing
        )


        # we want to obtain two (sets of) flat sheet bodies:
        # 1.  The plinth footprint (which I am calling the 'support' (not to be
        #     confused with 'support' in the context of 3d printing)
        # 2.  The embossed design.

        supportSheetBodies : Sequence[adsk.fusion.BRepBody] = tuple(
            deleteInnerLoops(rankZeroSheetBody)
            for rankZeroSheetBody in sheetBodiesGroupedByRank[0]
        )

        rankZeroSheetBodies = sheetBodiesGroupedByRank[0]
        oddRankSheetBodies = tuple(
            sheetBody
            for r in range(len(sheetBodiesGroupedByRank))
            for sheetBody in sheetBodiesGroupedByRank[r]
            if r % 2 == 1
        )

        # supportSheetBodies = tuple(
        #     fscadBody.brep 
        #     for rankZeroSheetBody in rankZeroSheetBodies
        #     for fscadBody in fscad.Hull(fscad.BRepComponent(rankZeroSheetBody)).bodies
        # )

        supportFscadComponent = fscad.BRepComponent(*supportSheetBodies, name=f"support"); 
        print(f"supportFscadComponent.mid: {(supportFscadComponent.mid().x, supportFscadComponent.mid().y, supportFscadComponent.mid().z)}")
        
        # supportFscadComponent.create_occurrence()
        # oddRankFscadComponent = fscad.BRepComponent(*oddRankSheetBodies, name=f"odd rank"); oddRankFscadComponent.create_occurrence()
        # rankZeroFscadComponent = fscad.BRepComponent(*rankZeroSheetBodies, name=f"rank zero"); rankZeroFscadComponent.create_occurrence()


        
        rootAngularSpan = 120 * degree
        letterRadialExtent = 1/4 * inch
        plinthRadialExtent = 1/4 * inch
        letterDraftAngle = - 4 *degree
        plinthDraftAngle = - 7 *degree
        # offsetCornerType =  adsk.fusion.OffsetCornerTypes.LinearOffsetCornerType  #.CircularOffsetCornerType  #.ExtendedOffsetCornerType
        offsetCornerType =  adsk.fusion.OffsetCornerTypes.ExtendedOffsetCornerType


        # rootAngularSpan = 10 * degree
        # letterRadialExtent =1 * millimeter
        # plinthRadialExtent = 1 * millimeter
        # letterDraftAngle = 0 *degree
        # plinthDraftAngle = 0 *degree


        rootRadius = ( supportFscadComponent.max().y - supportFscadComponent.min().y ) * radian / rootAngularSpan


        print(f"rootRadius: {rootRadius}")
        # rootRadius = 3*centimeter
        letterRadiusMax = rootRadius
        letterRadiusMin = letterRadiusMax - letterRadialExtent

        plinthRadiusMax = letterRadiusMin
        plinthRadiusMin = plinthRadiusMax - plinthRadialExtent
        
        

        cylinderOrigin = (0,0,rootRadius + 1*centimeter)       
        cylinderAxisDirection = xHat

        # these argument values will be splatted into all calls to
        # wrapSheetBodiesAroundCylinder() .
        commonWrappingArguments = {
            'cylinderOrigin'         : cylinderOrigin ,
            'cylinderAxisDirection'  : cylinderAxisDirection ,
            'rootRadius'             : rootRadius ,
            'offsetCornerType'       : offsetCornerType
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

        # wrappedLetterSheetsAtMaxRadius = wrapSheetBodiesAroundCylinder(
        #     sheetBodies    = letterSheetsAtMaxRadius,
        #     wrappingRadius = letterRadiusMax,
        #     **commonWrappingArguments
        # )

        # wrappedLetterSheetsAtMinRadius = wrapSheetBodiesAroundCylinder(
        #     sheetBodies    = letterSheetsAtMinRadius,
        #     wrappingRadius = letterRadiusMin,
        #     **commonWrappingArguments
        # )

        # wrappedPlinthSheetsAtMaxRadius = wrapSheetBodiesAroundCylinder(
        #     sheetBodies    = plinthSheetsAtMaxRadius,
        #     wrappingRadius = plinthRadiusMax,
        #     **commonWrappingArguments
        # )

        # wrappedPlinthSheetsAtMinRadius = wrapSheetBodiesAroundCylinder(
        #     sheetBodies    = plinthSheetsAtMinRadius,
        #     wrappingRadius = plinthRadiusMin,
        #     **commonWrappingArguments
        # )

        # fscad.BRepComponent(
        #     *wrappedLetterSheetsAtMaxRadius, 
        #     name=f"wrappedLetterSheetsAtMaxRadius"
        # ).create_occurrence()

        # fscad.BRepComponent(
        #     *wrappedLetterSheetsAtMinRadius, 
        #     name=f"wrappedLetterSheetsAtMinRadius"
        # ).create_occurrence()

        # fscad.BRepComponent(
        #     *wrappedPlinthSheetsAtMaxRadius, 
        #     name=f"wrappedPlinthSheetsAtMaxRadius"
        # ).create_occurrence()

        # fscad.BRepComponent(
        #     *wrappedPlinthSheetsAtMinRadius, 
        #     name=f"wrappedPlinthSheetsAtMinRadius"
        # ).create_occurrence()

        edifiedPlinthBodies = extrudeDraftAndWrapSheetbodiesAroundCylinder(
            sheetBodies = supportSheetBodies,
            wrappingRadiusStart = plinthRadiusMax,
            wrappingRadiusEnd = plinthRadiusMin,
            draftAngle = plinthDraftAngle ,
            **commonWrappingArguments
        )

        fscad.BRepComponent(
            *edifiedPlinthBodies, 
            name=f"edifiedPlinthBodies"
        ).create_occurrence()

        edifiedLetterBodies = extrudeDraftAndWrapSheetbodiesAroundCylinder(
            sheetBodies = oddRankSheetBodies,
            wrappingRadiusStart = letterRadiusMax,
            wrappingRadiusEnd = letterRadiusMin,
            draftAngle = letterDraftAngle ,
            **commonWrappingArguments
        )

        fscad.BRepComponent(
            *edifiedLetterBodies, 
            name=f"edifiedLetterBodies"
        ).create_occurrence()
    fscad.run_design(design_func=design1, message_box_on_error=False, re_raise_exceptions=True)
    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass















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
        

