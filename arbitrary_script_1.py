
print("this is an arbitrary script that is being used as a placeholder for testing the system of programmatically running scripts in Fusion.")

import adsk.core, adsk.fusion, adsk.cam, traceback
import datetime
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






def run(context=None):
    ui = None
    try:
        printDebuggingMessage("ahoy matey")
        app = adsk.core.Application.get()
        ui = app.userInterface
        printDebuggingMessage("ahoy matey 2")
        # ui.messageBox('hello script')
        ui.palettes.itemById('TextCommands').writeText(str(datetime.datetime.now()) + "\t" + 'Hello from ' + __file__)
        # app.userInterface.commandDefinitions.itemById('ScriptsManagerCommand').execute(adsk.core.NamedValues.create())
        # app.userInterface.commandDefinitions.itemById('RunScriptCommand').execute(adsk.core.NamedValues.create())
        # app.userInterface.commandDefinitions.itemById('PythonInteractiveCommand').execute(adsk.core.NamedValues.create())
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

# run()
