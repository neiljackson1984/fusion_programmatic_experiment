
print("this is an arbitrary script that is being used as a placeholder for testing the system of programmatically running scripts in Fusion.")

import adsk.core, adsk.fusion, adsk.cam, traceback
import datetime
import tempfile
import os
import pathlib

def app() -> adsk.core.Application: return adsk.core.Application.get()
def ui() -> adsk.core.UserInterface: return app().userInterface

def run(context:dict=None):
    ui().palettes.itemById('TextCommands').writeText(str(datetime.datetime.now()) + "\t" + 'xxxHello from ' + __file__)
    textCommandToExecute = "NotificationCenter.Toast"
    textCommandToExecute = "Debug.Toast"
    result :str = app().executeTextCommand("NotificationCenter.Toast")
    ui().palettes.itemById('TextCommands').writeText(textCommandToExecute)
    ui().palettes.itemById('TextCommands').writeText(result)




