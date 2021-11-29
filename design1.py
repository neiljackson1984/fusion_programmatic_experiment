import adsk.core, adsk.fusion, traceback
from typing import Any, Dict, Optional, Sequence, Union
from .braids.fscad.src.fscad import fscad as fscad
import traceback
import pathlib


from . import clay_stamp
from .utility import *

def run(context:dict):
 
    def design1() -> None:
        pathOfBuildDirectory = pathlib.Path(__file__).parent.joinpath('build')
        pathOfBuildDirectory.mkdir(exist_ok = True, parents=True)


        if not pathOfBuildDirectory.is_dir():
            print(f"attempting to create the build directory: {pathOfBuildDirectory}")
            pathOfBuildDirectory.mkdir(exist_ok = True)


        pathOfSvgFile                             = pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg')
        pathOfOutputFile                          = pathlib.Path(pathOfBuildDirectory).joinpath(pathOfSvgFile.name).with_suffix('.f3d')
        clay_stamp.makeClayStamp(
            # parameters controlling the svg import process:                                           
            pathOfSvgFile                             = pathOfSvgFile.resolve().as_posix(),
            pathOfOutputFile                          = pathOfOutputFile.resolve().as_posix(),
            # pathOfSvgFile                             = pathlib.Path(__file__).parent.joinpath('test_logo1.svg'),
            svgNativeLengthUnit                       = ((1/2 * inch)/36.068069458007805),
            translateAsNeededInOrderToPlaceMidPoint   = True,
                                                                                                                                
            #parameters controlling the stamp sans handle:                                                    
            rootAngularSpan                           = 120 * degree,
            letterRadialExtent                        = 1/4 * inch,
            plinthRadialExtent                        = 1/4 * inch,
            letterDraftAngle                          = - 4 *degree,
            plinthDraftAngle                          = - 7 *degree,
            offsetCornerType                          = adsk.fusion.OffsetCornerTypes.ExtendedOffsetCornerType,
            doMultipleLoftSegments                    = False,
            maximumAllowedRadialExtentOfLoftSegment   = 0 ,
                                                                                                                                
            #parameters controlling the handle:                                                            
            handlePathExtentZ                         =  25 * millimeter,
            handlePathExtentY                         =  40 * millimeter,
            handlePathRoundingRadius                  =  10 * millimeter,
            handleProfileExtentX                      =  15 * millimeter,
            handleProfileExtentY                      =  6  * millimeter,
            handleProfileRoundingRadius               =  2  * millimeter,
            handleToPlinthFilletRadius                =  6  * millimeter,
            flatBackFillThickness                     =  3  * millimeter
        )


    fscad.run_design(design_func=design1, message_box_on_error=False, re_raise_exceptions=True)
    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass




