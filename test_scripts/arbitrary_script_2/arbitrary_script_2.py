
print("this is an arbitrary script that is being used as a placeholder for testing the system of programmatically running scripts in Fusion.")

import adsk.core, adsk.fusion, adsk.cam, traceback
import datetime
import tempfile
import os
import pathlib


pathOfDebuggingLog = os.path.join(tempfile.gettempdir(), pathlib.Path(__file__).with_suffix('.log').name)

def printDebuggingMessage(x: str):
    global pathOfDebuggingLog
    logEntry = str(datetime.datetime.now()) + "\t" + x
    print(logEntry)
    try:
        with open(pathOfDebuggingLog ,'a') as reportFile:
            reportFile.write(logEntry + "\n")
    except:
        pass






def run(context:dict=None):
    ui = None
    try:
        printDebuggingMessage("ahoy matey")
        app = adsk.core.Application.get()
        ui = app.userInterface
        printDebuggingMessage("ahoy matey 2")
        # ui.messageBox('hello script')
        ui.palettes.itemById('TextCommands').writeText(str(datetime.datetime.now()) + "\t" + 'Hello from ' + __file__)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        printDebuggingMessage('Failed:\n{}'.format(traceback.format_exc()))

