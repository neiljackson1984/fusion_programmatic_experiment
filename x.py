# This is an add-in for Fusion 360 that will allow Fusion to be remotely controlled via RPyC,
# mainly for the purpose of commanding Fusion to run an arbitrary script.
# create a command in Fusion 360 to
# run an arbitrary python script in the current session.
# The goal is to have an executable that can be passed the path of the python script that we want to run,
# and then the executable will somehow communicate with this add-in and trigger the running of the script within the fusion 360 session.
#  How will we communicate with the add-in?  Poissibilities: add-in listens on a tcp port.  add-in watches a file or a named pipe.  
# What does python have in the way of Inter-process communication libraries.
# RPyC is a python-specific remote-procedure-call system that works over tcp.

import adsk.core, adsk.fusion, traceback
import math
import pathlib
import os
import sys
import datetime
import json

pathOfDebuggingLog = "C:\\work\\fusion_programmatic_experiment\\report2.txt"

def printDebuggingMessage(x: str):
    global pathOfDebuggingLog
    logEntry = str(datetime.datetime.now()) + "\t" + x
    print(logEntry)
    try:
        with open(pathOfDebuggingLog ,'a') as reportFile:
            reportFile.write(logEntry + "\n")
    except:
        pass
    # or
    # global app
    # if app.userInterface:
    #     app.userInterface.messageBox(x)





import threading



import rpyc
from rpyc.core import SlaveService
from rpyc.lib import setup_logger
from rpyc.utils.server import ThreadedServer, ForkingServer, OneShotServer


# import runpy
# runpy.run_path("C:\\Users\\Admin\\AppData\\Local\\Autodesk\\webdeploy\\production\\48ac19808c8c18863dd6034eee218407ecc49825\\Python\\vscode\\pre-run.py", run_name='__main__')
# import debugpy
# print(dir(debugpy))

sys.path.append("C:\\Users\\Admin\\.vscode\\extensions\\ms-python.python-2021.6.944021595\\pythonFiles\\lib\\python")
import debugpy

# sys.path.append(os.path.join(os.path.dirname(__file__)))
# from bolt import *




# specify the toolbar where you want to insert this command (for simplicity, we are going to insert 
# it directly into a toolbar rather than into a panel within a toolbar.
toolbarId = 'QAT' 
commandId = 'x'
pathOfCommandResourcesFolder = './resources'
attributeGroupName = "64fcb3b29c37466888d375e10f971704"

myCustomEventId = 'scriptRunRequested_customEvent'
customEvent = None

# global set of event handlers to keep them referenced for the duration of the command
handlers = []

# global list of all toolbarControls and commandDefinitions that we created, which we need to keepo track of so that we can delete them
# in the stop() method.
toolbarControls = []
commandDefinitions = []

app :adsk.core.Application = None
ui :adsk.core.UserInterface = None



class XCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.CommandEventArgs):
        # global server
        printDebuggingMessage('XCommandExecuteHandler::notify was called.' + "\n")
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            printDebuggingMessage('args.firingEvent.name: ' + args.firingEvent.name + "\n")
            printDebuggingMessage('args.firingEvent: ' + str(args.firingEvent) + "\n")
            printDebuggingMessage('args.command.execute: ' + str(args.command.execute) + "\n")
            printDebuggingMessage('args.command.destroy: ' + str(args.command.destroy) + "\n")
            
            # rpyc.lib.setup_logger()
            # server = ThreadedServer(
            #     SlaveService,
            #     hostname='localhost',
            #     port=18812,
            #     reuse_addr=True,
            #     ipv6=False, 
            #     authenticator=None,
            #     registrar=None, 
            #     auto_register=False
            # )
            # server.start()
            # server = OneShotServer(
            #     SlaveService,
            #     hostname='localhost',
            #     port=18812,
            #     reuse_addr=True,
            #     ipv6=False, 
            #     authenticator=None,
            #     registrar=None, 
            #     auto_register=False
            # )
            # server.start()

            # # Get the active design.
            # design = adsk.fusion.Design.cast(app.activeProduct)
            # rootComponent = design.rootComponent
            # ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
            
            # # if len(scriptedComponents) == 0:
            # if len(ScriptedComponent.getAllScriptedComponentsInAFusionDesign(design)) < 3:
            #     Bolt.create(design.rootComponent)
            # #Note: each "instance" of a scripted component class shall correspond to one unique fusion component, 
            # # and that fusion component shall have a single occurence.


            args.isValidResult = True

        except:
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

class XCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.CommandEventArgs):
        printDebuggingMessage('XCommandDestroyHandler::notify was called.' + "\n")
        try:
            printDebuggingMessage('args.firingEvent.name: ' + args.firingEvent.name + "\n")
            printDebuggingMessage('args.firingEvent: ' + str(args.firingEvent) + "\n")
            printDebuggingMessage('args.command.execute: ' + str(args.command.execute) + "\n")
            printDebuggingMessage('args.command.destroy: ' + str(args.command.destroy) + "\n")
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
        printDebuggingMessage("XCommandCreatedHandler::notify was called with firingEvent: " + str(args.firingEvent) + "\n")
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


class YCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self, theFunction):
        self._theFunction = theFunction
        super().__init__()        
    def notify(self, args):
        printDebuggingMessage("YCommandCreatedHandler::notify was called with firingEvent: " + str(args.firingEvent))
        try:
            self._theFunction(args)
        except:
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))



class ReportingApplicationCommandEventHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self):
        super().__init__()        
    def notify(self, args: adsk.core.ApplicationCommandEventArgs):
        if(args.commandId == 'SelectCommand'): return
        
        printDebuggingMessage(
            'ReportingApplicationCommandEventHandler::notify was called with \n' 
            + "\t" + "args.commandDefinition.id: " + str(args.commandDefinition.id) + "\n" 
            + "\t" + "args.commandId: " + str(args.commandId) + "\n" 
            + "\t" + "args.firingEvent: " + str(args.firingEvent) + "\n"
            + "\t" + "args.firingEvent.name: " + str(args.firingEvent.name) + "\n"
            + "\t" + "args.firingEvent.objectType: " + str(args.firingEvent.objectType) + "\n"
            + "\t" + "args.firingEvent.sender: " + str(args.firingEvent.sender) + "\n"
            + "\t" + "args.firingEvent.sender.objectType: " + str(args.firingEvent.sender.objectType) + "\n"
            + "\t" + "args.objectType: " + str(args.objectType) + "\n"
        )

class ReportingCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()        
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        printDebuggingMessage(
            'ReportingCommandCreatedEventHandler::notify was called with \n' 
            + "\t" + "args.command: " + str(args.command) + "\n" 
            # + "\t" + "args.commandDefinition.id: " + str(args.commandDefinition.id) + "\n" 
            # + "\t" + "args.commandId: " + str(args.commandId) + "\n" 
            # + "\t" + "args.firingEvent: " + str(args.firingEvent) + "\n"
            # + "\t" + "args.firingEvent.name: " + str(args.firingEvent.name) + "\n"
            # + "\t" + "args.firingEvent.objectType: " + str(args.firingEvent.objectType) + "\n"
            # + "\t" + "args.firingEvent.sender: " + str(args.firingEvent.sender) + "\n"
            # + "\t" + "args.firingEvent.sender.objectType: " + str(args.firingEvent.sender.objectType) + "\n"
            + "\t" + "args.objectType: " + str(args.objectType) + "\n"
        )


class ThreadEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self,args):
        try:
            # Make sure a command isn't running
            if ui.activeCommand != 'SelectCommand':
                ui.commandDefinitions.itemById('SelectCommand').execute()

            # Get the value from the JSON data passed through the event.
            eventArgs = json.loads(args.additionalInfo)
            
            printDebuggingMessage("eventArgs: " + str(eventArgs))       
            action=eventArgs['action']
            # actionArguments=eventArgs['arguments']


            if action == 'runScript':
                defaultActionArguments = {
                    'pathOfScript': None,
                    'debugMode': False
                }
                actionArguments = {**defaultActionArguments, **(eventArgs['arguments'] )}
                pathOfScript=actionArguments['pathOfScript'] 
                printDebuggingMessage("actionArguments: " + str(actionArguments))       
                # ui.messageBox('pathOfScript: ' + pathOfScript)
                import runpy
                runpy.run_path(pathOfScript)

        except: 
            printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))
# I am declaring server as a global thinking that the scope in which server is declared
# affects what is accessible (or how) via RPyC.  I am not entirely clear on the relationship
# between the scope in which server is declared and the resultant visibility of objects through RPyC.
# (aLl else equal, I think it would be cleaner to declare server in the function-body scope of daemonMain.)
server = ThreadedServer(
    SlaveService,
    hostname='localhost',
    port=18812,
    reuse_addr=True,
    ipv6=False, 
    authenticator=None,
    registrar=None, 
    auto_register=False
)

def daemonMain():
    """ daemonMain() is the function that will be run in a daemon thread.  We will create an RPyC server object,
    and wait for requests. """
    rpyc.lib.setup_logger()
    # server.close()
    server.start()

daemonThread = threading.Thread(target=daemonMain, daemon=True)

def run(context):
    global commandId
    global toolbarId
    global app
    global ui
    global commandDefinitions
    global toolbarControls
    global server
    try:
        app  = adsk.core.Application.get()
        ui = app.userInterface
        # product = app.activeProduct
        # design = adsk.fusion.Design.cast(product)
        # if not design:
        #     app.userInterface.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
        #     return 
        #check the command exists or not
        commandDefinition = ui.commandDefinitions.itemById(commandId)
        if commandDefinition:
            commandDefinition.deleteMe()
            commandDefinition = None

        if not commandDefinition:
            commandDefinition = ui.commandDefinitions.addButtonDefinition(
                #id=
                commandId,
                # name=
                'Create Bolt',
                # tooltip=
                'Create a bolt.',
                # resourceFolder=
                pathOfCommandResourcesFolder
            )
        commandDefinitions.append(commandDefinition)

        myCommandCreatedHandler = XCommandCreatedHandler()
        handlers.append(myCommandCreatedHandler) # keep the handler referenced beyond this function
        commandDefinition.commandCreated.add(myCommandCreatedHandler)




        myReportingApplicationCommandCreatedEventHandler = ReportingApplicationCommandEventHandler()
        handlers.append(myReportingApplicationCommandCreatedEventHandler)
        ui.commandCreated.add(myReportingApplicationCommandCreatedEventHandler)
        
        myReportingCommandCreatedEventHandler1 = ReportingCommandCreatedEventHandler()
        handlers.append(myReportingCommandCreatedEventHandler1)
        # ui.commandDefinitions.itemById('RunScriptCommand').commandCreated.add(myReportingCommandCreatedEventHandler2)
        commandDefinition.commandCreated.add(myReportingCommandCreatedEventHandler1)

        myReportingCommandCreatedEventHandler2 = ReportingCommandCreatedEventHandler()
        handlers.append(myReportingCommandCreatedEventHandler2)
        ui.commandDefinitions.itemById('ScriptsManagerCommand').commandCreated.add(myReportingCommandCreatedEventHandler2)


        myReportingCommandCreatedEventHandler3 = ReportingCommandCreatedEventHandler()
        handlers.append(myReportingCommandCreatedEventHandler3)
        ui.commandDefinitions.itemById('RunScriptCommand').commandCreated.add(myReportingCommandCreatedEventHandler3)

        # Fusion does not seem to be firing the CommandCreated event of built-in command definitions.


        myReportingCommandTermninatedEventHandler = ReportingApplicationCommandEventHandler()
        handlers.append(myReportingCommandTermninatedEventHandler)
        ui.commandTerminated.add(myReportingCommandTermninatedEventHandler)

        myReportingCommandStartingEventHandler = ReportingApplicationCommandEventHandler()
        handlers.append(myReportingCommandStartingEventHandler)
        ui.commandStarting.add(myReportingCommandStartingEventHandler)

        # Register the custom event and connect the handler.
        global customEvent
        customEvent = app.registerCustomEvent(myCustomEventId)
        myThreadEventHandler = ThreadEventHandler()
        customEvent.add(myThreadEventHandler)
        handlers.append(myThreadEventHandler)


        # delete any existing control with the same name in the destination toolbar that might happen to exist already
        existingToolbarControl = app.userInterface.toolbars.itemById(toolbarId).controls.itemById(commandId)
        if existingToolbarControl:
            existingToolbarControl.deleteMe()
        
        # insert the command into the toolbar
        toolbarControl = app.userInterface.toolbars.itemById(toolbarId).controls.addCommand(commandDefinition)
        toolbarControl.isVisible = True
        toolbarControls.append(toolbarControl)

        toolbarControl2 = app.userInterface.toolbars.itemById(toolbarId).controls.addCommand(ui.commandDefinitions.itemById('RunScriptCommand'))
        toolbarControl2.isVisible = True
        toolbarControls.append(toolbarControl2)

        pathOfReportFile = pathlib.Path(__file__).parent.joinpath("report.txt").resolve()
        with open(pathOfReportFile ,'w') as reportFile:
            print("see " + str(pathOfReportFile))
            for commandDefinition in app.userInterface.commandDefinitions:
                reportFile.write(commandDefinition.id + "\n")
        # inputs = adsk.core.NamedValues.create()
        # commandDefinition.execute(inputs)
        global daemonThread
        daemonThread.start()
        # rpyc.lib.setup_logger()
        # server.start()

        # prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire
        # adsk.autoTerminate(False)



    except:
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        global commandDefinitions
        global toolbarControls
        for commandDefinition in commandDefinitions:
            commandDefinition.deleteMe()
        commandDefinitions = []

        for toolbarControl in toolbarControls:
            toolbarControl.deleteMe()
        toolbarControls = []

        # kill the daemon thread.
        global daemonThread
        daemonThread.join(timeout=0)
        server.close()
        app.unregisterCustomEvent(myCustomEventId)
    except:
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))
