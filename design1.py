import os, sys
import adsk.core, adsk.fusion, traceback
import inspect
import pprint; 

# sys.path.append(os.path.join(os.path.dirname(__file__)))
from . import scripted_component
from . import bolt



def app() -> adsk.core.Application: return adsk.core.Application.get()
def ui() -> adsk.core.UserInterface: return app().userInterface

def run(context:dict):
    # a = 3 + 3
    # pass
    # raise Exception("xxxbogus exception")
    # return
    
    design = adsk.fusion.Design.cast(app().activeProduct)
    rootComponent = design.rootComponent
    # ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    print("ScriptedComponent.__subclasses__(): " + str(scripted_component.ScriptedComponent.__subclasses__()))

    pp=pprint.PrettyPrinter(indent=4, width=80, depth=2, compact=False); 
    pp.pprint(
        inspect.getmembers(scripted_component.ScriptedComponent.__subclasses__()[0])
    )
    print(scripted_component.ScriptedComponent.__subclasses__()[0].__qualname__)
    print(scripted_component.ScriptedComponent.__subclasses__()[0].__name__)


    if len(scripted_component.ScriptedComponent.getAllScriptedComponentsInAFusionDesign(design)) < 3:
        bolt.Bolt.create(design.rootComponent)

    # scripted_component.ScriptedComponent.updateAllScriptedComponentsInAFusionDesign(design)
    # prevent this module from being terminated when the script returns
    # adsk.autoTerminate(False)

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

# def stop():
#     pass