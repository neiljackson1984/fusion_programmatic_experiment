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
        # 1.  The plinth footprint.
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

        supportFscadComponent = fscad.BRepComponent(*supportSheetBodies, name=f"support")
        oddRankFscadComponent = fscad.BRepComponent(*oddRankSheetBodies, name=f"oddRank")
        
        

        # fscad.BRepComponent(*oddRankSheetBodies, name=f"oddRankSheetBodies").create_occurrence()
        # fscad.BRepComponent(*supportSheetBodies, name=f"supportSheetBodies").create_occurrence()
        # getAllSheetBodiesFromSketch() (due to Fusion's underlying sketch region logic) gives
        # us a set of non-overlapping sheets.  We want to categorize these sheets by rank, so that 
        # we can say that the outer edge of the rank 0 sheets is the boundary of the plinth footprint,
        # and all sheets having ((rank >0) and (rank is odd)) are the "ink" sheets (the ink on the page).
        
        supportFscadComponent.create_occurrence()
        oddRankFscadComponent.create_occurrence()


        cylinderRadius = 7*inch       
        cylinderOrigin = adsk.core.Point3D.create(0,0,cylinderRadius)       
        cylinderAxisDirection = castToVector3D(xHat)     
        cylinderLength = 20*inch
        
        
        
        # destinationSurface : adsk.core.Surface = adsk.core.Cylinder.create(
        #     origin=cylinderOrigin,
        #     axis=cylinderAxisDirection,
        #     radius = cylinderRadius
        # )
        # # destinationSurface.evaluator.getParamAnomaly(): [True, (0.0, 0.0), (6.283185307179586, -3.141592653589793), (), (), (True, False)]
        # # uRange: (0.0, 0.0)
        # # vRange: (-3.141592653589793, 3.141592653589793)


        cylinderForWrapping = cylinderByStartEndRadius(
            startPoint = castToPoint3D(castTo3dArray(cylinderOrigin) - castTo3dArray(cylinderAxisDirection) * cylinderLength/2),
            endPoint = castToPoint3D(castTo3dArray(cylinderOrigin) + castTo3dArray(cylinderAxisDirection) * cylinderLength/2),
            radius=cylinderRadius
        )
        cylinderForWrapping.name = "cylinder for wrapping"
        
        cylinderForWrapping.create_occurrence()
        destinationSurface = cylinderForWrapping.side.brep.geometry

        highlight(
            # tuple(destinationSurface.evaluator.getIsoCurve(0,isUDirection=True)),
            adsk.core.Circle3D.createByCenter(
                center = cylinderOrigin,
                normal = cylinderAxisDirection,
                radius = cylinderRadius
            ),
            **makeHighlightParams("cylinder preview")
        )
        print(f"destinationSurface.evaluator.getParamAnomaly(): {destinationSurface.evaluator.getParamAnomaly()}")
        # fscad._create_construction_point(rootComponent(), )

        pRange : adsk.core.BoundingBox2D = destinationSurface.evaluator.parametricRange()
        
        uRange = (pRange.minPoint.x, pRange.maxPoint.x)
        vRange = (pRange.minPoint.y, pRange.maxPoint.y)

        print(f"uRange: {uRange}\nvRange: {vRange}")
        #
        # uRange: (0.0, 0.0)
        # vRange: (-3.141592653589793, 3.141592653589793)
        #


        xRange = (supportFscadComponent.min().x, supportFscadComponent.max().x)
        yRange = (supportFscadComponent.min().y, supportFscadComponent.max().y)

        morphedSheetBodies = wrapSheetBodiesAroundCylinder(
            sheetBodies=rankZeroSheetBodies,
            destinationSurface=destinationSurface
        )



        wrappedSupportFscadComponent = fscad.BRepComponent(
            *morphedSheetBodies, 
            name=f"wrapped support"
        )

        
        
        wrappedSupportFscadComponent.create_occurrence()
       


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