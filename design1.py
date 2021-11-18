import os, sys
import adsk.core, adsk.fusion, traceback
import inspect
import pprint
from typing import Any, Dict, Optional, Sequence, Union
# from . import scripted_component
from . import bit_holder
# from .scripted_component import ScriptedComponent
# from .bolt import Bolt
from .braids.fscad.src.fscad import fscad as fscad
from .highlight import *
import uuid
import traceback
import time

import pathlib
import itertools

from .bit_holder_utility import *

def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent

_brep = None
def temporarayBrepManager() -> adsk.fusion.TemporaryBRepManager:
    # caching the brep is a workaround for a weird bug where an exception from calling a TemporaryBRepManager method
    # and then catching the exception causes TemporaryBRepManager.get() to then throw the same error that was previously
    # thrown and caught. Probably some weird SWIG bug or something.
    global _brep
    if not _brep:
        _brep = adsk.fusion.TemporaryBRepManager.get()
    return _brep


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

def makeHighlightParams(name: Optional[str] = None) -> Dict[str,Any]:
    """
    this produces a dict containing the optional params for the highlight()
    function  (intended to be double-star splatted into the arguments list) 
    that will cause the hihglight function to produce a new named
    component just tom contain the hihglights -- the benfit of having a set of
    highlights in a component is that we can then toggle the visibility of the
    hihghlights in the ui by togglinng the visibility of the occurence of the
    componet.
    """
    componentToReceiveTheCustomGraphics = (
        rootComponent()
        .occurrences
        .addNewComponent(adsk.core.Matrix3D.create())
        .component
    )
    componentToReceiveTheCustomGraphics.name = (name if name is not None else "anonymous_highlight")
    return {
        'colorEffect':  next(globalColorCycle),
        'customGraphicsGroupToReceiveTheCustomGraphics' : componentToReceiveTheCustomGraphics.customGraphicsGroups.add()
    }


def run(context:dict):
 
    def design1():
        
        # bit_holder.getCannedBitHolders()['1/4-inch hex shank driver bits holder'].create_occurrence()
        tempOccurrence = fscad._create_component(
            parent_component = fscad.root(), 
            name="temp"
        )
        sketch = tempOccurrence.component.sketches.add(tempOccurrence.component.xYConstructionPlane, tempOccurrence)
        # sketch.importSVG(pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg').as_posix(),0 ,0, 1)
        sketch.importSVG(pathlib.Path(__file__).parent.joinpath('test_logo.svg').as_posix(),0 ,0, 1)

        # we want to obtain two (sets of) flat sheet bodies:
        # 1.  The plinth footprint (which I am calling the 'support' (not to be
        #     confused with 'support' in the context of 3d printing)
        # 2.  The embossed design.

        allSheetBodiesFromSketchGroupedByRank = getAllSheetBodiesFromSketchGroupedByRank(sketch)
        rankZeroSheetBodies = allSheetBodiesFromSketchGroupedByRank[0]
        oddRankSheetBodies = tuple(
            sheetBody
            for r in range(len(allSheetBodiesFromSketchGroupedByRank))
            for sheetBody in allSheetBodiesFromSketchGroupedByRank[r]
            if r % 2 == 1
        )
        supportSheetBodies = tuple(
            fscadBody.brep 
            for rankZeroSheetBody in rankZeroSheetBodies
            for fscadBody in fscad.Hull(fscad.BRepComponent(rankZeroSheetBody)).bodies
        )
        # The supportSheetBodies is just the union of all sheet bodies.
        # The above method is probably an enormously wasteful way to compute it, 
        # but oh well.

        # we want to construct sheet bodie(s) based on the outer loop(s) of rankZeroSheetBodies

        # for rank in range(len(allSheetBodiesFromSketchGroupedByRank)):
        #     fscad.BRepComponent(*allSheetBodiesFromSketchGroupedByRank[rank], name=f"rank {rank} sheet bodies").create_occurrence()

        # rankZeroFscadComponent = fscad.BRepComponent(*rankZeroSheetBodies, name=f"rank zero"); rankZeroFscadComponent.create_occurrence()
        supportFscadComponent = fscad.BRepComponent(*supportSheetBodies, name=f"support"); supportFscadComponent.create_occurrence()
        oddRankFscadComponent = fscad.BRepComponent(*oddRankSheetBodies, name=f"oddRank"); oddRankFscadComponent.create_occurrence()

        rootRadius = 3*centimeter
        letterRadiusMax = rootRadius
        plinthRadiusMax = rootRadius - (1/4)*inch
        plinthRadiusMin = plinthRadiusMax - (1/4*inch)



        cylinderRadius = 3*centimeter
        cylinderOrigin = (0,0,cylinderRadius + 1*centimeter)       
        cylinderAxisDirection = xHat
        rootRadius = 3*centimeter

        # these argument values will be splatted into all calls to
        # wrapSheetBodiesAroundCylinder() .
        commonWrappingArguments = {
            'cylinderOrigin'         : cylinderOrigin ,
            'cylinderAxisDirection'  : cylinderAxisDirection ,
            'rootRadius'             : rootRadius
        }

        #These are the sheets that, along with rootRadius define the shapes in
        # (length, angle) space: (We are not doing the circumferential
        # stretching to account for differing radii here)-- that gets done by
        # wrapSheetBodiesAroundCylinder() (by using both the rootRadius and the
        # wrappingRadius parameters).
        letterSheetsAtMaxRadius = oddRankSheetBodies
        plinthSheetsAtMaxRadius = supportSheetBodies
        #TODO: construct plinthSheetsAtMinRadius by offsetting plinthSheetsAtMaxRadius (in order to produce the desired draft angle)
        plinthSheetsAtMinRadius = plinthSheetsAtMaxRadius # just for testing

        #TODO: construct letterSheetsAtMinRadius by offsetting letterSheetsAtMaxRadius (in order to produce the desired draft angle)
        letterSheetsAtMinRadius = letterSheetsAtMaxRadius


        highlight(
            # tuple(destinationSurface.evaluator.getIsoCurve(0,isUDirection=False)),
            adsk.core.Circle3D.createByCenter(
                center = castToPoint3D(cylinderOrigin),
                normal = castToVector3D(cylinderAxisDirection),
                radius = cylinderRadius
            ),
            **makeHighlightParams("cylinder preview")
        )

        wrappedLetterSheetsAtMaxRadius = wrapSheetBodiesAroundCylinder(
            sheetBodies    = letterSheetsAtMaxRadius,
            wrappingRadius = letterRadiusMax,
            **commonWrappingArguments
        )

        wrappedLetterSheetsAtMinRadius = wrapSheetBodiesAroundCylinder(
            sheetBodies    = letterSheetsAtMinRadius,
            wrappingRadius = plinthRadiusMax,
            **commonWrappingArguments
        )

        wrappedPlinthSheetsAtMaxRadius = wrapSheetBodiesAroundCylinder(
            sheetBodies    = plinthSheetsAtMaxRadius,
            wrappingRadius = plinthRadiusMax,
            **commonWrappingArguments
        )

        wrappedPlinthSheetsAtMinRadius = wrapSheetBodiesAroundCylinder(
            sheetBodies    = plinthSheetsAtMinRadius,
            wrappingRadius = plinthRadiusMin,
            **commonWrappingArguments
        )

        fscad.BRepComponent(
            *wrappedLetterSheetsAtMaxRadius, 
            name=f"wrappedLetterSheetsAtMaxRadius"
        ).create_occurrence()

        fscad.BRepComponent(
            *wrappedLetterSheetsAtMinRadius, 
            name=f"wrappedLetterSheetsAtMinRadius"
        ).create_occurrence()

        fscad.BRepComponent(
            *wrappedPlinthSheetsAtMaxRadius, 
            name=f"wrappedPlinthSheetsAtMaxRadius"
        ).create_occurrence()

        fscad.BRepComponent(
            *wrappedPlinthSheetsAtMinRadius, 
            name=f"wrappedPlinthSheetsAtMinRadius"
        ).create_occurrence()

    #monkeypatching traceback with vscode-compatible link formatting
    initialTracebackStackSummaryFormatMethod = formatStackSummary
    traceback.StackSummary.format = formatStackSummary
    fscad.run_design(design_func=design1, message_box_on_error=False)
    traceback.StackSummary.format = initialTracebackStackSummaryFormatMethod
    # run_design(design_func=design2, message_box_on_error=False)
    # print(traceback.format_tb(sys.last_traceback))

    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass


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

#monkeypatching traceback with vscode-compatible link formatting
traceback.StackSummary.format = formatStackSummary
















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
        

