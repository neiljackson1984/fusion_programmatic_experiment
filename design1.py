import adsk.core, adsk.fusion, traceback
from typing import Any, Dict, Optional, Sequence, Union
from .braids.fscad.src.fscad import fscad as fscad
import traceback
import pathlib
import datetime
import json


from .utility import *


def run(context:dict):
 
    def design1_clayStamp() -> None:
        from . import clay_stamp
        import zipfile

        pathOfBuildDirectory = pathlib.Path(__file__).parent.joinpath('build')
        pathOfBuildDirectory.mkdir(exist_ok = True, parents=True)
        


        timestampOfThisRun =  datetime.datetime.now()

        pathOfArtifactZipFile = pathlib.Path(pathOfBuildDirectory).joinpath("{:%Y%m%d%H%M%S}".format(timestampOfThisRun) + ".zip") 
        pathOfTestReportFile = pathlib.Path(pathOfBuildDirectory).joinpath("{:%Y%m%d%H%M%S}".format(timestampOfThisRun) + "--test_report.json") 
        pathsOfArtifactFiles=[]
        

        fileSpecificParameterOverrides = {
            'eXotic logo 1 2.svg': {
                'svgNativeLengthUnit': ((1/2 * inch)/36.068069458007805)
            },
            'test_logo2.svg': {
                'svgNativeLengthUnit': ((1/2 * inch)/36.068069458007805)
            }
        }


        testParameterGrid = {
            'rootAngularSpan': [ 
                # 10 * degree,
                # 40 * degree, 
                120 * degree
            ],
            'letterRadialExtent' : [
                # 1 * millimeter, 
                3 * millimeter, 
                # 1/4*inch
            ],
            'plinthRadialExtent' : [
                1/4*inch 
            ],
            'letterDraftAngle': [
                # 0, 
                # -1* degree, 
                -4* degree, 
                # -7* degree, 
                # -10*degree 
            ],
            'plinthDraftAngle': [
                -7* degree   
            ],
            'pathOfSvgFile':  [
                # pathlib.Path(__file__).parent.joinpath('eXotic logo 1 2.svg').resolve().as_posix(),
                # pathlib.Path(__file__).parent.joinpath('test_logo1.svg').resolve().as_posix(),
                pathlib.Path(__file__).parent.joinpath('test_logo2.svg').resolve().as_posix()
            ]
        }
        #testParameterGrid is a dict whose keys are parameter names and whose values are
        # values of the corresponding parameter, which we are interested in
        # testing. We will run the process for each member of the cartesian
        # product of these parameter values.

        testPoints = list(
            map(
                dict,
                itertools.product(
                    *(
                        [
                            (key, value)
                            for value in testParameterGrid[key]
                        ]
                        for key in testParameterGrid
                    )
                )
            )
        )


        commonDefaultParameters = { 
            'svgNativeLengthUnit'                       : 1 * millimeter,
            'translateAsNeededInOrderToPlaceMidPoint'   : True,
                                                                                                                                
            #parameters controlling the stamp sans handle:                                                    
            # 'rootAngularSpan'                           : 120 * degree,
            # 'letterRadialExtent'                        : 1/4 * inch,
            # 'plinthRadialExtent'                        : 1/4 * inch,
            # 'letterDraftAngle'                          : - 4 *degree,
            # 'plinthDraftAngle'                          : - 7 *degree,
            # 'offsetCornerType'                          : adsk.fusion.OffsetCornerTypes.ExtendedOffsetCornerType,
            'offsetCornerType'                          : adsk.fusion.OffsetCornerTypes.LinearOffsetCornerType,
            'doMultipleLoftSegments'                    : False,
            'maximumAllowedRadialExtentOfLoftSegment'   : 1*millimeter ,
                                                                                                                                
            #parameters controlling the handle:                                                            
            'handlePathExtentZ'                         :  25 * millimeter,
            'handlePathExtentY'                         :  63 * millimeter,
            'handlePathRoundingRadius'                  :  10 * millimeter,
            'handleProfileExtentX'                      :  15 * millimeter,
            'handleProfileExtentY'                      :  6  * millimeter,
            'handleProfileRoundingRadius'               :  2  * millimeter,
            'handleToPlinthFilletRadius'                :  6  * millimeter,
            'flatBackFillThickness'                     :  3  * millimeter
        }

        testReport = {}
        testReport['timestampOfThisRun'] = f"{timestampOfThisRun}"
        testReport['commonDefaultParameters'] = commonDefaultParameters
        testReport['testParameterGrid'] = testParameterGrid
        testReport['fileSpecificParameterOverrides'] = fileSpecificParameterOverrides

        testReport['testResults'] = []

        for testPointIndex in range(len(testPoints)):
            print(f"now processing test point {testPointIndex} of {len(testPoints)}.")
            

            
            testParameters = testPoints[testPointIndex]


            gridIndex = [
                testParameterGrid[key].index(testParameters[key])
                for key in testParameterGrid
            ]
            testResult = {}
            testResult['testIndex'] = testPointIndex
            testResult['gridIndex'] = gridIndex
            testResult['testParameters'] = testParameters

            pathOfSvgFile = testPoints[testPointIndex]['pathOfSvgFile']
            pathOfOutputFile = pathlib.Path(pathOfBuildDirectory).joinpath(
                "{:%Y%m%d%H%M%S}".format(timestampOfThisRun) 
                + "--"
                + f"{testPointIndex}"
                + "--"
                + "-".join(map(str,gridIndex))
                # + "--"
                # + pathlib.Path(pathOfSvgFile).stem 
                + ".f3d"
            ).resolve().as_posix()      

            resolvedParameters = {
                **commonDefaultParameters,
                # parameters controlling the svg import process:                                           
                'pathOfSvgFile'                             : pathOfSvgFile,
                'pathOfOutputFile'                          : pathOfOutputFile,
                **fileSpecificParameterOverrides.get(pathlib.Path(pathOfSvgFile).name,{}),
                **testParameters
            }
            testResult['resolvedParameters'] = resolvedParameters


            errorOccured=False
            errorMessage=""
            nameOfArtifactFile=""
            try:
                clay_stamp.makeClayStamp(**resolvedParameters)
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
    # design1 = design1_clayStamp

    def design1_bitHolder() -> None:
        from . import bit_holder
        # v = adsk.core.Vector3D.create(0,0,0)
        # v = adsk.core.Vector3D.create(False, False, False)

        # myBitHolderSegment = bit_holder.BitHolderSegment(
        #     # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
        #     # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
        #     bit=bit_holder.Bit(
        #         labelText="\\floodWithInk"
        #         #labelText="ABC"
        #     ),
        #     minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
        #     doLabelRetentionLip=True,
        #     directionsOfEdgesThatWeWillAddALabelRetentionLipTo=(
        #         bit_holder.xHat,
        #         # bit_holder.yHat,
        #         # bit_holder.zHat,
        #     )
        # )
        
        # myBitHolderSegment.create_occurrence()


        if False:
            myBitHolder = bit_holder.BitHolder(
                segments = [
                    bit_holder.BitHolderSegment(
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
                        bit= bit_holder.Bit(
                                labelText="\\floodWithInk"
                                #labelText="ABC"
                            ),
                        minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
                        doLabelRetentionLip=True,
                        directionsOfEdgesThatWeWillAddALabelRetentionLipTo=(
                            bit_holder.xHat,
                            # bit_holder.yHat,
                            # bit_holder.zHat,
                        )
                    )
                    for i in range(6)
                ] + [
                    bit_holder.BitHolderSegment(
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.EMBOSS,
                        # labelSculptingStrategy=bit_holder.LabelSculptingStrategy.ENGRAVE
                        bit= bit_holder.Socket(
                                driveSize   = 3/8 * bit_holder.inch,
                                length      = 25.96 * bit_holder.millimeter,
                                nominalUnit = 1*bit_holder.inch,
                                nominalSize = 3/8 * bit_holder.inch,
                                outerDiameter = 17.18 * bit_holder.millimeter
                            ),
                        labelFontHeight=(4.75 * bit_holder.millimeter, 3.2 * bit_holder.millimeter),
                        minimumAllowedLabelToZMinOffset=3*bit_holder.millimeter,
                        doLabelRetentionLip=False
                    )
                ]
            )
            
        # myBitHolder = bit_holder.getCannedBitHolders()['bondhus_hex_drivers_holder']
        # myBitHolder.create_occurrence()

        # startTime = time.time()
        # bit_holder.getCannedBitHolders()
        # endTime = time.time()
        # print("duration of first bit_holder.getCannedBitHolders(): %f" % (endTime-startTime))


        # startTime = time.time()
        # bit_holder.getCannedBitHolders()
        # endTime = time.time()
        # print("duration of second bit_holder.getCannedBitHolders(): %f" % (endTime-startTime))

        # startTime = time.time()
        # # bitHolderArray = bit_holder.makeBitHolderArray(*list(bit_holder.getCannedBitHolders().values())[0:1]*3)
        
        # myBitHolder = list(bit_holder.getCannedBitHolders().values())[0]
        # initialSegments = myBitHolder.segments
        # x = initialSegments[0]
        # # y = x.copy()

        # # myBitHolder.segments = (initialSegments[0].copy(), initialSegments[0].copy(), initialSegments[1])
        # myBitHolder.segments = (initialSegments[i] for i in (0,1,1,1,0))
        # bitHolderArray = bit_holder.makeBitHolderArray(*[myBitHolder]*3)

        # endTime = time.time()
        # print("duration of makeBitHolderArray: %f" % (endTime-startTime))

        # startTime = time.time()
        # # bitHolderArray = bit_holder.makeBitHolderArray(*bit_holder.getCannedBitHolders().values())
        # bitHolderArray = bit_holder.makeBitHolderArray(
        #     *(v for k,v in sorted(bit_holder.getCannedBitHolders().items()))
        # )
        # endTime = time.time()
        # print("duration of makeBitHolderArray: %f" % (endTime-startTime))





        # pathOfStepFileToImport=pathlib.Path(__file__).parent.joinpath('all_bit_holders_from_onshape.step').resolve()
        # allBitHoldersFromOnshape = bit_holder.import_step_file(pathOfStepFileToImport.as_posix(), pathOfStepFileToImport.stem)




        # # # onlyInA = fscad.Difference(a, b)
        # # # onlyInB = fscad.Difference(b, a)
        # # intersection = fscad.Intersection(a,b)

        # # # onlyInA.name = 'a_only'
        # # # onlyInB.name = 'b_only'
        # # intersection.name = 'a_and_b'


        # startTime = time.time()
        # bitHolderArray.create_occurrence()
        # allBitHoldersFromOnshape.create_occurrence()
        
        # a = bitHolderArray
        # b = allBitHoldersFromOnshape
        # union = fscad.Union(bitHolderArray, allBitHoldersFromOnshape, name='union')
        # onlyA = fscad.Difference(union, b, name='onlyA')
        # onlyA.create_occurrence()
        # onlyB = fscad.Difference(union, a, name= 'onlyB')
        # onlyB.create_occurrence()
        # intersection = fscad.Difference(union, onlyA, onlyB, name='intersection')
        # intersection.create_occurrence()
        # # onlyInA.create_occurrence()
        # # onlyInB.create_occurrence()
        # # intersection.create_occurrence()

        # endTime = time.time()
        # print("duration of bitHolderArray.create_occurrence(): %f" % (endTime-startTime))

        bit_holder.getCannedBitHolders()['1/4-inch hex shank driver bits holder'].create_occurrence()
    # design1 = design1_bitHolder
    
    def design1_toughcaseModule():  
        from . import toughcase
        toughcase.ToughCaseModule().create_occurrence()            
    design1 = design1_toughcaseModule
    

    fscad.run_design(design_func=design1, message_box_on_error=False, re_raise_exceptions=True)
    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass




