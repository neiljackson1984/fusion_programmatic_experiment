import adsk.core, adsk.fusion, traceback
from typing import Any, Dict, Optional, Sequence, Union
from .braids.fscad.src.fscad import fscad as fscad
import traceback
import pathlib
import datetime
import json

from . import clay_stamp
from .utility import *

import zipfile

def run(context:dict):
 
    def design1() -> None:
        pathOfBuildDirectory = pathlib.Path(__file__).parent.joinpath('build')
        pathOfBuildDirectory.mkdir(exist_ok = True, parents=True)
        


        timestampOfThisRun =  datetime.datetime.now()

        pathOfArtifactZipFile = pathlib.Path(pathOfBuildDirectory).joinpath("{:%Y%m%d%H%M%S}".format(timestampOfThisRun) + ".zip") 
        pathOfTestReportFile = pathlib.Path(pathOfBuildDirectory).joinpath("{:%Y%m%d%H%M%S}".format(timestampOfThisRun) + "--test_report.json") 
        pathsOfArtifactFiles=[]
        

        fileSpecificParameterOverrides = {
            'eXotic logo 1 2.svg': {
                'svgNativeLengthUnit': ((1/2 * inch)/36.068069458007805)
            }
        }

        # points in parameter space that we want to test.
        testPoints = [
            {
                'rootAngularSpan'    : rootAngularSpan,
                'letterRadialExtent' : letterRadialExtent,
                'plinthRadialExtent' : plinthRadialExtent,
                'letterDraftAngle'   : letterDraftAngle,
                'plinthDraftAngle'   : plinthDraftAngle,
                'pathOfSvgFile'      : pathOfSvgFile
            }
            for rootAngularSpan in [ 
                # 10 * degree,
                # 40 * degree, 
                120 * degree
            ]
            for letterRadialExtent in [
                1 * millimeter, 
                # 3 * millimeter, 
                # 1/4*inch
            ]
            for plinthRadialExtent in [
                1/4*inch 
            ]
            for plinthDraftAngle   in [ 
                -7*degree 
            ]
            for letterDraftAngle   in [
                # 0, 
                -1* degree, 
                # -4* degree, 
                # -7* degree, 
                #   -10*degree 
            ]
            for pathOfSvgFile in [
                pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg').resolve().as_posix(),
                pathlib.Path(__file__).parent.joinpath('test_logo3.svg').resolve().as_posix()
            ]
        ]

        commonParameters = { 
            'svgNativeLengthUnit'                       : 1 * millimeter,
            'translateAsNeededInOrderToPlaceMidPoint'   : True,
                                                                                                                                
            #parameters controlling the stamp sans handle:                                                    
            # 'rootAngularSpan'                           : 120 * degree,
            # 'letterRadialExtent'                        : 1/4 * inch,
            # 'plinthRadialExtent'                        : 1/4 * inch,
            # 'letterDraftAngle'                          : - 4 *degree,
            # 'plinthDraftAngle'                          : - 7 *degree,
            'offsetCornerType'                          : adsk.fusion.OffsetCornerTypes.ExtendedOffsetCornerType,
            # 'offsetCornerType'                          : adsk.fusion.OffsetCornerTypes.LinearOffsetCornerType,
            'doMultipleLoftSegments'                    : False,
            'maximumAllowedRadialExtentOfLoftSegment'   : 1*millimeter ,
                                                                                                                                
            #parameters controlling the handle:                                                            
            'handlePathExtentZ'                         :  25 * millimeter,
            'handlePathExtentY'                         :  40 * millimeter,
            'handlePathRoundingRadius'                  :  10 * millimeter,
            'handleProfileExtentX'                      :  15 * millimeter,
            'handleProfileExtentY'                      :  6  * millimeter,
            'handleProfileRoundingRadius'               :  2  * millimeter,
            'handleToPlinthFilletRadius'                :  6  * millimeter,
            'flatBackFillThickness'                     :  3  * millimeter
        }

        testReport = {}
        testReport['timestampOfThisRun'] = f"{timestampOfThisRun}"
        testReport['commonParameters'] = commonParameters
        testReport['testResults'] = []

        for testPointIndex in range(len(testPoints)):
            print(f"now processing test point {testPointIndex} of {len(testPoints)}.")
            
            
            testParameters = testPoints[testPointIndex]
            testResult = {}
            testResult['testParameters'] = testParameters

            pathOfSvgFile = testPoints[testPointIndex]['pathOfSvgFile']
            pathOfOutputFile = pathlib.Path(pathOfBuildDirectory).joinpath(
                "{:%Y%m%d%H%M%S}".format(timestampOfThisRun) 
                + "--"
                + f"{testPointIndex}"
                + "--"
                + pathlib.Path(pathOfSvgFile).stem 
                + ".f3d"
            ).resolve().as_posix()      

            parameters = {
                **commonParameters,
                # parameters controlling the svg import process:                                           
                'pathOfSvgFile'                             : pathOfSvgFile,
                'pathOfOutputFile'                          : pathOfOutputFile,
                **fileSpecificParameterOverrides.get(pathlib.Path(pathOfSvgFile).name,{}),
                **testParameters
            }
            testResult['parameters'] = parameters


            errorOccured=False
            errorMessage=""
            nameOfArtifactFile=""
            try:
                clay_stamp.makeClayStamp(**parameters)
            except Exception as e:
                errorOccured=True
                errorMessage=f"{e}"
                print(f"encountered exception while working on testPoints[{testPointIndex}]: {e}")
            else:
                pathsOfArtifactFiles.append(pathOfOutputFile)
                nameOfArtifactFile = pathlib.Path(pathOfOutputFile).name
            
            testResult['errorOccured'] = errorOccured
            testResult['errorMessage'] = errorMessage
            testResult['nameOfArtifactFile'] = nameOfArtifactFile
            testReport['testResults'].append(testResult)

        with open(pathOfTestReportFile, 'w') as file:
            json.dump(testReport, file, indent=4)
        
        pathsOfArtifactFiles.append(pathOfTestReportFile)

        # create a zip file containing all builtArtifactFiles
        artifactZipFile = zipfile.ZipFile(file=pathOfArtifactZipFile, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)
        for pathOfArtifactFile in pathsOfArtifactFiles:
            print(f"Now zipping {pathOfArtifactFile}")
            artifactZipFile.write(filename=pathOfArtifactFile, arcname=pathlib.Path(pathOfArtifactFile).name)
        artifactZipFile.close()


    fscad.run_design(design_func=design1, message_box_on_error=False, re_raise_exceptions=True)
    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass




