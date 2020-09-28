#Author-Autodesk Inc.
#Description-Create bolt

import adsk.core, adsk.fusion, traceback
import math
import pathlib
import os
import sys
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__)))
from bolt import *


toolbarControl = None

#specify the toolbar where you want to insert this command (for simplicity, we are going to insert it directly into a toolbar rather than into a panel within a toolbar.
toolbarId = 'QAT' 
commandId = 'x'
commandResources = './resources'
attributeGroupName = "64fcb3b29c37466888d375e10f971704"

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()


commandDefinition = None

def printDebuggingMessage(x: str):
    print(
        str(datetime.datetime.now()) + "\t" + x
    )
    # or
    # global app
    # if app.userInterface:
    #     app.userInterface.messageBox(x)

class XCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        printDebuggingMessage('XCommandExecuteHandler::notify was called.')
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender

           
            # Get the active design.
            design = adsk.fusion.Design.cast(app.activeProduct)
            rootComponent = design.rootComponent
            ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
            
            # if len(scriptedComponents) == 0:
            if len(ScriptedComponent.getAllScriptedComponentsInAFusionDesign(design)) < 3:
                Bolt.create(design.rootComponent)
            #Note: each "instance" of a scripted component class shall correspond to one unique fusion component, 
            # and that fusion component shall have a single occurence.


            args.isValidResult = True

        except:
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

class XCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        printDebuggingMessage('XCommandDestroyHandler::notify was called.')
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            # adsk.terminate()
            pass
        except:
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

class XCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        printDebuggingMessage("XCommandCreatedHandler::notify was called with firingEvent: " + str(args.firingEvent))
        try:
            args.command.isRepeatable = False
            
            xCommandExecuteHandler = XCommandExecuteHandler()
            args.command.execute.add(xCommandExecuteHandler)
            # onExecutePreview = XCommandExecuteHandler()
            args.command.executePreview.add(xCommandExecuteHandler)
            # handlers.append(onExecutePreview)
            handlers.append(xCommandExecuteHandler)

            xCommandDestroyHandler = XCommandDestroyHandler()
            args.command.destroy.add(xCommandDestroyHandler)
            handlers.append(xCommandDestroyHandler)

            #define the inputs
            # args.command.commandInputs.addStringValueInput ( 'boltName'        , 'Bolt Name'         ,          Bolt.defaultBoltName                                             )
            # args.command.commandInputs.addValueInput       ( 'headDiameter'    , 'Head Diameter'     , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultHeadDiameter    ) )
            # args.command.commandInputs.addValueInput       ( 'shankDiameter'   , 'Shank Diameter'    , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultShankDiameter   ) )
            # args.command.commandInputs.addValueInput       ( 'headHeight'      , 'Head Height'       , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultHeadHeight      ) )
            # args.command.commandInputs.addValueInput       ( 'length'          , 'Length'            , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultLength          ) )
            # args.command.commandInputs.addValueInput       ( 'cutAngle'        , 'Cut Angle'         , 'deg'  , adsk.core.ValueInput.createByReal( Bolt.defaultCutAngle        ) )
            # args.command.commandInputs.addValueInput       ( 'chamferDistance' , 'Chamfer Distance'  , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultChamferDistance ) )
            # args.command.commandInputs.addValueInput       ( 'filletRadius'    , 'Fillet Radius'     , 'cm'   , adsk.core.ValueInput.createByReal( Bolt.defaultFilletRadius    ) )
        except:
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

class ReportingApplicationCommandEventHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self):
        super().__init__()        
    def notify(self, args: adsk.core.ApplicationCommandEventArgs):
        printDebuggingMessage(
            'ReportingApplicationCommandEventHandler::notify was called with \n' 
            + "\t" + "args.commandDefinition.id: " + str(args.commandDefinition.id) + "\n" 
            + "\t" + "args.commandId: " + str(args.commandId) + "\n" 
            + "\t" + "args.firingEvent.name: " + str(args.firingEvent.name) + "\n"
        )


def run(context):
    global commandId
    global toolbarId
    global app
    global commandDefinition
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            app.userInterface.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return 
        #check the command exists or not
        commandDefinition = app.userInterface.commandDefinitions.itemById(commandId)
        if commandDefinition:
            commandDefinition.deleteMe()
            commandDefinition = None

        if not commandDefinition:
            commandDefinition = app.userInterface.commandDefinitions.addButtonDefinition(
                #id=
                commandId,
                # name=
                'Create Bolt',
                # tooltip=
                'Create a bolt.',
                # resourceFolder=
                commandResources
            )

        myCommandCreatedHandler = XCommandCreatedHandler()
        myReportingCommandCreatedEventHandler = ReportingApplicationCommandEventHandler()
        commandDefinition.commandCreated.add(myCommandCreatedHandler)
        # keep the handler referenced beyond this function
        handlers.append(myCommandCreatedHandler)

        app.userInterface.commandCreated.add(myReportingCommandCreatedEventHandler)
        handlers.append(myReportingCommandCreatedEventHandler)

        

        # delete any existing control with the same name in the destination toolbar that might happen to exist already
        existingToolbarControl = app.userInterface.toolbars.itemById(toolbarId).controls.itemById(commandId)
        if existingToolbarControl:
            existingToolbarControl.deleteMe()
        
        # insert the command into the toolbar
        global toolbarControl
        toolbarControl = app.userInterface.toolbars.itemById(toolbarId).controls.addCommand(commandDefinition)
        toolbarControl.isVisible = True

        pathOfReportFile = pathlib.Path(__file__).parent.joinpath("report.txt").resolve()
        with open(pathOfReportFile ,'w') as reportFile:
            print("see " + str(pathOfReportFile))
            for commandDefinition in app.userInterface.commandDefinitions:
                reportFile.write(commandDefinition.id + "\n")

        inputs = adsk.core.NamedValues.create()
        commandDefinition.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        # adsk.autoTerminate(False)



    except:
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        global commandDefinition
        if commandDefinition:
            commandDefinition.deleteMe()
            commandDefinition = None
        global toolbarControl
        if toolbarControl:
            toolbarControl.deleteMe()
            toolbarControl = None

    except:
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))
