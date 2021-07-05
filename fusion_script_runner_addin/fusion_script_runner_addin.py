
"""

Note: running a script or add-in via this add-in will not cause the script/add-in to appear 
in Fusion360's "Scripts and Add-Ins" dialog.  This is one of the ways in which the action of this add-in is not
exactly identical to the action of manual commands issued in Fusion360's user interface.
"""

# The structure and much of the function of this code is inspired by Ben Gruver's fusion_idea_addin

import adsk.core
import adsk.fusion
import hashlib
import http.client
# from http.server import HTTPServer, BaseHTTPRequestHandler
import http.server
import importlib
import importlib.util
import io
import json
import logging
import logging.handlers
import os
import re
import socket
import socketserver
import struct
import sys
import threading
import traceback
from typing import Optional, Callable
import urllib.parse
import tempfile
import shutil
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 


import rpyc
import rpyc.core
# import rpyc.lib
import rpyc.utils.server

# from rpyc.core import SlaveService
# from rpyc.lib import setup_logger
# from rpyc.utils.server import Server, ThreadedServer, ForkingServer, OneShotServer


NAME_OF_THIS_ADDIN = 'fusion_script_runner_addin'
RUN_SCRIPT_REQUESTED_EVENT_ID = f"{NAME_OF_THIS_ADDIN}_run_script_requested"
ERROR_DIALOG_EVENT_ID = f"{NAME_OF_THIS_ADDIN}_error_dialog"

PORT_NUMBER_FOR_RPYC_SLAVE_SERVER = 18812
PORT_NUMBER_FOR_HTTP_SERVER = 19812

def app() -> adsk.core.Application: return adsk.core.Application.get()
def ui() -> adsk.core.UserInterface: return app().userInterface

logger = logging.getLogger(NAME_OF_THIS_ADDIN)
logger.propagate = False

class AddIn(object):
    def __init__(self):
        self._run_script_requested_event_handler    : Optional[RunScriptRequestedEventHandler]  = None
        self._run_script_requested_event            : Optional[adsk.core.CustomEvent]           = None
        self._error_dialog_event_handler            : Optional[ErrorDialogEventHandler]         = None
        self._error_dialog_event                    : Optional[adsk.core.CustomEvent]           = None
        self._logging_file_handler                  : Optional[logging.Handler]                 = None
        self._logging_dialog_handler                : Optional[logging.Handler]                 = None
        self._http_server                           : Optional[http.server.HTTPServer]          = None
        self._rpyc_slave_server                     : Optional[rpyc.utils.server.Server]        = None
        self._toolbarControls                       : list[adsk.core.ToolbarControl]            = []
        self._commandDefinitions                    : list[adsk.core.CommandDefinition]         = []
        self._command1                              : Optional[SimpleFusionCustomCommand]       = None

    def start(self):
        
        # logging-related setup, in its own try block because, once logging is properly set up,
        # we will use the logging infrastructure to log error messages in the Except block,
        # but here, before logging infrasturcture is set up, the Except block will report
        # error messages in a more primitive way.
        try:
            self._logging_file_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), f"{NAME_OF_THIS_ADDIN}_log.txt"),
                maxBytes=2**20,
                backupCount=1)
            self._logging_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(self._logging_file_handler)
            # logger.setLevel(logging.WARNING)
            logger.setLevel(logging.DEBUG)

            self._error_dialog_event = app().registerCustomEvent(ERROR_DIALOG_EVENT_ID)
            self._error_dialog_event_handler = ErrorDialogEventHandler()
            self._error_dialog_event.add(self._error_dialog_event_handler)

            self._logging_dialog_handler = FusionErrorDialogLoggingHandler()
            self._logging_dialog_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logging_dialog_handler.setLevel(logging.FATAL)
            logger.addHandler(self._logging_dialog_handler)
        except Exception:
            # The logging infrastructure may not be set up yet, so we directly show an error dialog instead
            ui().messageBox(f"Error while starting {NAME_OF_THIS_ADDIN}.\n\n%s" % traceback.format_exc())
            return

        try:
            try:
                app().unregisterCustomEvent(RUN_SCRIPT_REQUESTED_EVENT_ID)
            except Exception:
                pass

            logger.debug("ahoy there")
            logger.debug("os.getcwd(): " + os.getcwd())

            self._run_script_requested_event = app().registerCustomEvent(RUN_SCRIPT_REQUESTED_EVENT_ID)
            self._run_script_requested_event_handler = RunScriptRequestedEventHandler()
            self._run_script_requested_event.add(self._run_script_requested_event_handler)

            # Ben Gruver would run the http server on a random port, to avoid conflicts when multiple instances of Fusion 360 are
            # running, and would have the client use SSDP to discover the correct desired port to connect to.
            # I am, at present, simplifying things and simply using a hard-coded port number.
            self._http_server = http.server.HTTPServer(("localhost", PORT_NUMBER_FOR_HTTP_SERVER), RunScriptHTTPRequestHandler)

            http_server_thread = threading.Thread(target=self.run_http_server, daemon=True)
            http_server_thread.start()

            self._rpyc_slave_server = rpyc.ThreadedServer(
                rpyc.SlaveService,
                hostname='localhost',
                port=PORT_NUMBER_FOR_RPYC_SLAVE_SERVER,
                reuse_addr=True,
                ipv6=False, 
                authenticator=None,
                registrar=None, 
                auto_register=False
            )

            rpyc_slave_server_thread = threading.Thread(target=self.run_rpyc_slave_server, daemon=True)
            rpyc_slave_server_thread.start()

            def myTestFunction(args: adsk.core.CommandEventArgs):
                logger.debug("myTestFunction was called.")

            self._command1 = SimpleFusionCustomCommand(name="neil_cool_command1", action=myTestFunction, app=app())

        except Exception:
            logger.fatal(f"Error while starting {NAME_OF_THIS_ADDIN}", exc_info=sys.exc_info())

    def run_http_server(self):
        logger.debug("starting http server: port=%d" % self._http_server.server_port)
        try:
            with self._http_server:
                self._http_server.serve_forever()
        except Exception:
            logger.fatal("Error occurred while starting the http server.", exc_info=sys.exc_info())

    def run_rpyc_slave_server(self):
        #TO DO: add exception handling
        self._rpyc_slave_server.start()

    def stop(self):
        if self._http_server:
            try:
                self._http_server.shutdown()
                self._http_server.server_close()
            except Exception:
                logger.error(f"Error while stopping {NAME_OF_THIS_ADDIN}'s HTTP server.", exc_info=sys.exc_info())
        self._http_server = None

        if self._rpyc_slave_server:
            try:
                self._rpyc_slave_server.close()
                # is it thread-safe to call the server's close() method here in a thread
                # other than the thread in which the server is running?
                # perhaps we need to .join(timeout=0) the thread in which the server is running and then 
                # run server's close() method.
            except Exception:
                logger.error(f"Error while stopping {NAME_OF_THIS_ADDIN}'s rpyc slave server.", exc_info=sys.exc_info())
        self._rpyc_slave_server = None

        #clean up any ui commands and controls that we may have created
        for commandDefinition in self._commandDefinitions:
            commandDefinition.deleteMe()
        self._commandDefinitions = []

        for toolbarControl in self._toolbarControls:
            toolbarControl.deleteMe()
        self._toolbarControls = []

        # clean up _run_script_requested_event and the associated handler:
        try:
            if self._run_script_requested_event_handler and self._run_script_requested_event:
                self._run_script_requested_event.remove(self._run_script_requested_event_handler)

            if self._run_script_requested_event:
                app().unregisterCustomEvent(RUN_SCRIPT_REQUESTED_EVENT_ID)
        except Exception:
            logger.error("Error while unregistering {NAME_OF_THIS_ADDIN}'s run_script event handler.",
                         exc_info=sys.exc_info())
        self._run_script_requested_event_handler = None
        self._run_script_requested_event = None

        del self._command1

        # clean up _error_dialog_event and the associated handler:
        try:
            if self._error_dialog_event_handler and self._error_dialog_event:
                self._error_dialog_event.remove(self._error_dialog_event_handler)

            if self._error_dialog_event:
                app().unregisterCustomEvent(ERROR_DIALOG_EVENT_ID)
        except Exception:
            logger.error(f"Error while unregistering {NAME_OF_THIS_ADDIN}'s error_dialog event handler.",
                         exc_info=sys.exc_info())
        self._error_dialog_event_handler = None
        self._error_dialog_event = None



        # clean up _logging_file_handler:
        try:
            if self._logging_file_handler:
                self._logging_file_handler.close()
                logger.removeHandler(self._logging_file_handler)
        except Exception:
            ui().messageBox(f"Error while closing {NAME_OF_THIS_ADDIN}'s file logger.\n\n%s" % traceback.format_exc())
        self._logging_file_handler = None

        # clean up _logging_dialog_handler:
        try:
            if self._logging_dialog_handler:
                self._logging_dialog_handler.close()
                logger.removeHandler(self._logging_dialog_handler)
        except Exception:
            ui().messageBox(f"Error while closing {NAME_OF_THIS_ADDIN}'s dialog logger.\n\n%s" % traceback.format_exc())
        self._logging_dialog_handler = None

class SimpleFusionCustomCommand(object):
    """ This class automates the housekeeping involved with creating a custom command linked to a toolbar button in Fusion """
    # Given the way Fusion uses the word "command" to refer to an action currently in progress rather than 
    # a meaning more closely aligned with my intuitive notion of command, which is something like "function",
    # it might make sense not to name this class "command", but use some other term like "function" "task" "procedure" "routine" etc.

    def __init__(self, name: str, action: Callable[[adsk.core.CommandEventArgs] , None], app: adsk.core.Application):
        self._name = name
        self._action = action
        self._commandId = self._name # TO-DO: ensure that the commandId is unique and doesn't contain any illegal characters.
        self._app = app
        self._resourcesDirectory = tempfile.TemporaryDirectory()
        logger.warning("self._resourcesDirectory.name: " + self._resourcesDirectory.name)
        logger.warning("sys.version: " + sys.version)

        iconText = self._name[0].capitalize()
        for imageSize in (16, 32, 64):
            img = Image.new(mode='RGB',size=(imageSize, imageSize),color='white')
            draw :ImageDraw.ImageDraw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf",imageSize)
            draw.text((imageSize/2,imageSize/2),iconText ,font=font, fill='black',anchor='mm')
            img.save(os.path.join(self._resourcesDirectory.name, f"{imageSize}x{imageSize}.png"))

        self._commandDefinition = self._app.userInterface.commandDefinitions.addButtonDefinition(
            #id=
            self._commandId,
            #name=
            self._name,
            #tootlip=
            self._name,
            #resourceFolder(optional)=
            # (i'm omitting the resourceFolder argument for now)
            self._resourcesDirectory.name
        )
        self._commandCreatedHandler = self.CommandCreatedEventHandler(owner=self)
        self._commandDefinition.commandCreated.add(self._commandCreatedHandler)
        self._commandEventHandler = self.CommandEventHandler(owner=self)
        self._toolbarControl : adsk.core.CommandControl = self._app.userInterface.toolbars.itemById('QAT').controls.addCommand(self._commandDefinition)
        self._toolbarControl.isVisible = True

    def __del__(self):
        self._commandDefinition.deleteMe()
        del self._commandDefinition
        self._toolbarControl.deleteMe()
        del self._toolbarControl
        self._resourcesDirectory.cleanup()
        del self._resourcesDirectory

    class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
        def __init__(self, owner: 'SimpleFusionCustomCommand'):
            super().__init__()
            self._owner = owner
        def notify(self, args: adsk.core.CommandCreatedEventArgs):
            args.command.execute.add(self._owner._commandEventHandler)
            args.command.destroy.add(self._owner._commandEventHandler)
            args.command.executePreview.add(self._owner._commandEventHandler)


    class CommandEventHandler(adsk.core.CommandEventHandler):
        def __init__(self, owner: 'SimpleFusionCustomCommand'):
            super().__init__()
            self._owner = owner
        def notify(self, args: adsk.core.CommandEventArgs):    
            if args.firingEvent.name == 'OnExecute':
                self._owner._action(args)

class RunScriptRequestedEventHandler(adsk.core.CustomEventHandler):
    """
    An event handler that can run a python script in the main thread of fusion 360, and initiate debugging.
    """

    def notify(self, args: adsk.core.CustomEventArgs):
        try:
            # logger.debug("RunScriptRequestedEventHandler::notify is running with args.additionalInfo " + args.additionalInfo)
            args = json.loads(args.additionalInfo)
            # logger.debug("RunScriptRequestedEventHandler::notify is running with args " + json.dumps(args))
            # ui().palettes.itemById('TextCommands').writeText('ahoy')
            
            script_path = args.get("script")
            # debug = int(args["debug"]
            debug = ( int(args["debug"]) if 'debug' in args else None )
            # pydevd_path = args["pydevd_path"]
            pydevd_path = args.get("pydevd_path")

            detach = script_path and debug

            if not script_path and not debug:
                logger.warning("No script provided and debugging not requested. There's nothing to do.")
                return

            
            if pydevd_path:
                sys.path.append(pydevd_path)
            
            
            try:
                if debug:
                    sys.path.append(os.path.join(pydevd_path, "pydevd_attach_to_process"))
                    try:
                        import attach_script
                        port = int(args["debug_port"])
                        logger.debug("Initiating attach on port %d" % port)
                        attach_script.attach(port, "localhost")
                        logger.debug("After attach")
                    except Exception:
                        logger.fatal("An error occurred while while starting debugger.", exc_info=sys.exc_info())
                    finally:
                        del(sys.path[-1])  # pydevd_attach_to_process dir

                if script_path:
                    script_path = os.path.abspath(script_path)
                    script_dir = os.path.dirname(script_path)

                    try:
                        # This mostly mimics the package name that Fusion uses when running the script
                        module_name = "__main__" + urllib.parse.quote(script_path.replace('.', '_'))
                        spec = importlib.util.spec_from_file_location(
                            module_name, script_path, submodule_search_locations=[script_dir])
                        module = importlib.util.module_from_spec(spec)

                        existing_module = sys.modules.get(module_name)
                        if existing_module and hasattr(existing_module, "stop"):
                            existing_module.stop({"isApplicationClosing": False})

                        self.unload_submodules(module_name)

                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        logger.debug("Running script")
                        module.run({"isApplicationStartup": False})
                    except Exception:
                        logger.fatal("Unhandled exception while importing and running script.",
                                     exc_info=sys.exc_info())
            finally:
                if detach:
                    try:
                        import pydevd
                        logger.debug("Detaching")
                        pydevd.stoptrace()
                    except Exception:
                        logger.error("Error while stopping tracing.", exc_info=sys.exc_info())
        except Exception:
            logger.fatal("An error occurred while attempting to start script.", exc_info=sys.exc_info())
        finally:
            if pydevd_path:
                del sys.path[-1]  # The pydevd dir

    @staticmethod
    def unload_submodules(module_name):
        search_prefix = module_name + '.'
        loaded_submodules = []
        for loaded_module_name in sys.modules:
            if loaded_module_name.startswith(search_prefix):
                loaded_submodules.append(loaded_module_name)
        for loaded_submodule in loaded_submodules:
            del sys.modules[loaded_submodule]


class ErrorDialogEventHandler(adsk.core.CustomEventHandler):
    """An event handler that shows an error dialog to the user."""

    # noinspection PyMethodMayBeStatic
    def notify(self, args):
        ui().messageBox(args.additionalInfo, f"{NAME_OF_THIS_ADDIN} error")


class FusionErrorDialogLoggingHandler(logging.Handler):
    """A logging handler that shows a error dialog to the user in Fusion 360."""

    def emit(self, record: logging.LogRecord) -> None:
        adsk.core.Application.get().fireCustomEvent(ERROR_DIALOG_EVENT_ID, self.format(record))


class RunScriptHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """An HTTP request handler that queues an event in the main thread of fusion 360 to run a script."""

    def do_POST(self):
        logger.debug("Got an http request.")
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length).decode()

        try:
            # logger.debug("RunScriptHTTPRequestHandler::do_POST is running with body " + body)
            request_json = json.loads(body)
            logger.debug("RunScriptHTTPRequestHandler::do_POST is running with request_json " + json.dumps(request_json))
            # logger.debug("type(request_json['message']): " + str(type(request_json['message'])))
 
            # It seems clunky to require that request_json["message"] be a string.  I think it makes more sense 
            # to allow it to be 
            # an object (in which case we need to stringify it before passing it to fireCustomEvent
            # because fireCustomEvent requires a string for its 'addionalInfo' argument.), but also 
            # handle the case where it is a string
            # (in which case we assume that it is the json-serialized version of the object.)

            app().fireCustomEvent( 
                RUN_SCRIPT_REQUESTED_EVENT_ID,  
                # request_json["message"]
                ( request_json['message'] if isinstance(request_json['message'], str) else json.dumps(request_json['message']))
            )
            # additionalInfo (the second argument to fireCustomeEvent()) is a string that will be retrievable in the notify(args) method of the 
            # customEventHandler
            # as args.additionalInfo 

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"done")
        except Exception:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())
            logger.error("An error occurred while handling http request.", exc_info=sys.exc_info())


addin = AddIn()

def run(context:dict):
    addin.start()

def stop(context:dict):
    logger.debug("stopping")
    addin.stop()
