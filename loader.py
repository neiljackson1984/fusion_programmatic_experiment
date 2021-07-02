""" This script's sole purpose is to load the add-in (possibly in debugging mode) 
We can invoke fusion like this:
Fusion360 --execute "Python.Run '<path of this loader script>'"

"""

print("this is the loader script.")

import adsk.core, adsk.fusion, adsk.cam, traceback
def foo(context=None):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('hello script')
        app.userInterface.commandDefinitions.itemById('ScriptsManagerCommand').execute(adsk.core.NamedValues.create())
        # app.userInterface.commandDefinitions.itemById('RunScriptCommand').execute(adsk.core.NamedValues.create())
        # app.userInterface.commandDefinitions.itemById('PythonInteractiveCommand').execute(adsk.core.NamedValues.create())
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

foo()
