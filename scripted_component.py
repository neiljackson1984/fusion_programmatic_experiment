import adsk.core, adsk.fusion, traceback
import datetime
from typing import Iterable


def printDebuggingMessage(x: str):
    print(
        str(datetime.datetime.now()) + "\t" + x
    )
    # or
    # global app
    # if app.userInterface:
    #     app.userInterface.messageBox(x)

# get all descendants of the given class.
def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses

class ScriptedComponent (object):
    """ 
    A ScriptedComponent is a wrapper around an adsk.fusion.Component

    """

    # this is a static constant that we use as the name of the "attribute group name" 
    # -- an identifier within Fusion that is associated with the metadata that we attach to 
    # Fusion entities using Fusion's "atttributes" system (a mechanism for attaching arbitrary third-party data 
    # to Fusion entities)
    attributeGroupName = "64fcb3b29c37466888d375e10f971704"

    # the official constructor is only to be used in cases where we have an existing fusion component that we want to
    # work with.  In the case, where we want to create a new fusion component (and the wrapping ScriptedComponent instance 
    # to go along with it), you should call the factory function that is a a static member of the Component class.
    # I want this constructor to be called only within the constructors of derived classes.
    def __init__(self, fusionComponent: adsk.fusion.Component):
        self._fusionComponent = fusionComponent
        printDebuggingMessage("ScriptedComponent::__init__ was called with self.__class__.__name__ being " + self.__class__.__name__)

    def findFirstTaggedEntity(self, tag: str) -> adsk.core.Base:
        return adsk.core.Attribute.cast(
            next(
                    filter(
                        lambda attribute: 
                            adsk.core.Attribute.cast(attribute).parent.parentComponent == self._fusionComponent
                            #this is playing fast and loose with types. Attribute::parent() returns a Base object, 
                            # which is not guaranteed to have a parentComponent property.
                            #we ought to handle the case where attribute.parent does not have a parentComponent property.
                            #also, we are completely ignoring the possibility of nested components/nested occurences.
                        ,
                        self._fusionComponent.parentDesign.findAttributes(ScriptedComponent.attributeGroupName, tag)
                    )
                )
            ).parent

    #virtual
    def update(self) -> None:
        pass


    @classmethod 
    def create(cls, parentFusionComponent: adsk.fusion.Component):
        newlyCreatedOccurence  = parentFusionComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        newlyCreatedFusionComponent = adsk.fusion.Component.cast(newlyCreatedOccurence.component)
        newlyCreatedFusionComponent.attributes.add(ScriptedComponent.attributeGroupName, "ScriptedComponent", "") # this is the special marker that designates a scripted component
        newlyCreatedFusionComponent.attributes.add(ScriptedComponent.attributeGroupName, "class", cls.__name__)
        return cls(newlyCreatedFusionComponent)

    @staticmethod
    def getAllScriptedComponentsInAFusionDesign( fusionDesign: adsk.fusion.Design ) -> Iterable['ScriptedComponent']:
        scriptedComponents = [
            adsk.fusion.Component.cast(adsk.core.Attribute.cast(attribute).parent) 
            for attribute in 
            fusionDesign.findAttributes(ScriptedComponent.attributeGroupName, "ScriptedComponent")
        ]

        scriptedComponents = []
        attribute: adsk.core.Attribute
        for attribute in fusionDesign.findAttributes(ScriptedComponent.attributeGroupName, "ScriptedComponent"):
            fusionComponent = adsk.fusion.Component.cast(attribute.parent)
            className = fusionComponent.attributes.itemByName(ScriptedComponent.attributeGroupName,"class").value
            klass = next(filter(lambda x: x.__name__ == className , inheritors(ScriptedComponent)))
            scriptedComponents.append(klass(fusionComponent))

        printDebuggingMessage("found " + str(len(scriptedComponents)) + " scripted components.")

        # printDebuggingMessage("found the following scripted components: " + 
        #     ", ".join(
        #         [
        #             scriptedComponent.name for scriptedComponent in scriptedComponents
        #         ]
        #     )
        # )

        return scriptedComponents

    @staticmethod
    def updateAllScriptedComponentsInAFusionDesign(fusionDesign: adsk.fusion.Design) -> None:
        for scriptedComponent in ScriptedComponent.getAllScriptedComponentsInAFusionDesign(fusionDesign):
            scriptedComponent.update()