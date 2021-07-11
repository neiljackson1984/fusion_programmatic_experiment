
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

import shutil

import datetime
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))
from simple_fusion_custom_command import SimpleFusionCustomCommand

 
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

debugging_started=False

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
        # self._toolbarControls                       : list[adsk.core.ToolbarControl]            = []
        # self._commandDefinitions                    : list[adsk.core.CommandDefinition]         = []
        # self._fusionCommand1                        : Optional[SimpleFusionCustomCommand]       = None
        self._simpleFusionCustomCommands            : list[SimpleFusionCustomCommand]           = []

    def start(self):
        
        # logging-related setup, in its own try block because, once logging is properly set up,
        # we will use the logging infrastructure to log error messages in the Except block,
        # but here, before logging infrasturcture is set up, the Except block will report
        # error messages in a more primitive way.
        try:
            self._logging_file_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), f"{NAME_OF_THIS_ADDIN}_log.log"),
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

            def myTestFunction(eventArgs: adsk.core.CommandEventArgs)  -> None:
                logger.debug("myTestFunction was called.")
                return None

            self._simpleFusionCustomCommands.append(SimpleFusionCustomCommand(name="neil_cool_command1", action=myTestFunction, app=app(), logger=logger))

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

        # #clean up any ui commands and controls that we may have created
        # for commandDefinition in self._commandDefinitions:
        #     commandDefinition.deleteMe()
        # self._commandDefinitions = []

        # for toolbarControl in self._toolbarControls:
        #     toolbarControl.deleteMe()
        # self._toolbarControls = []

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

        # del self._fusionCommand1

        del self._simpleFusionCustomCommands

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

class RunScriptRequestedEventHandler(adsk.core.CustomEventHandler):
    """
    An event handler that can run a python script in the main thread of fusion 360, and initiate debugging.
    """

    def notify(self, args: adsk.core.CustomEventArgs):
        try:
            # logger.debug("RunScriptRequestedEventHandler::notify is running with args.additionalInfo " + args.additionalInfo)
            
            # collect the arguments:
            _args :dict = json.loads(args.additionalInfo)
            script_path     = _args.get("script")
            debug           = bool(_args.get("debug"))
            debugpy_path    = _args.get("debugpy_path")
            port            = int(_args.get("debug_port",0))

            if not script_path and not debug:
                logger.warning("No script provided and debugging not requested. There's nothing to do.")
                return

            if debug:
                # make sure that debugging is running.
                if not debugpy_path:
                    logger.warning("We have been instructed to do debugging, but you have not provided the necessary debugpy_path.  Therefore, we can do nothing.")
                    return
                initialSystemPath=sys.path.copy()
                sys.path.append(debugpy_path)
                import debugpy
                import debugpy._vendored
                with debugpy._vendored.vendored(project='pydevd'):
                    from _pydevd_bundle.pydevd_constants import get_global_debugger
                    from pydevd import PyDB
                    import pydevd
                sys.path=initialSystemPath
                # I hope that it won't screw anything up to replace the sys.path value with a newly-created list (rather than modifying the existing list).
                    
                global debugging_started
                if not debugging_started and get_global_debugger() is not None :  
                    logger.debug("Our debugging_started flag is cleared, and yet the global debugger object exists (possibly left over from a previous run/stop cycle of this add in), so we will go ahead and set the debugging_started flag.")
                    debugging_started = True  
                    addin._simpleFusionCustomCommands.append(SimpleFusionCustomCommand(name="D_indicator", app=app(), logger=logger)) 
                # We are assuming that if the global debugger object exists, then debugging is active and configured as desired.
                # I am not sure that this is always a safe assumption, but oh well.

                # ensure that debugging is started:
                #  ideally, we would look for an existing global debugger with the correct configuration
                # in order to determine whether debugging was started, rather than maintaining our own blind debugging_started flag.
                # the problem is that our flag can be wrong in the case where this add-in was started with debugging already active (started
                # by a previous run/stop cycle of this add in).  
                # Also, we should be doing something to stop debugging when this add-in is stopped, rather than just leaving it running, which we are doing now.
                # It seems that pydevd, or, at least the parts of the pydevd behavior that debugpy exposes, is not geared toward stopping the debugging, only starting it.
                # what about pydevd.stoptrace() ? -- that's what Ben Gruver does.
                if not debugging_started:
                    logger.debug("Commencing listening on port %d" % port)
                    
                    # debugpy.listen(port)
                    (lambda : debugpy.listen(port))()
                    # the code-reachability analysis system that is built into VS code (is this Pylance?) falsely 
                    # believes that the debugpy.listen()
                    # function will always result in an exception, and therefore regards all code below this point
                    # as unreachable, which causes vscode to display all code below this point in a dimmed color.
                    # I find this so annoying that I have wrapped the debugpy.listen() in a lambda function
                    # that I immediately call.  This seems to be sufficient to throw the code reachability analysis system 
                    # off the scent, and hopefully will not change the effect of the code.
                
                    class LoggingDapMessagesListener(pydevd.IDAPMessagesListener):
                        # @overrides(pydevd.IDAPMessagesListener.after_receive)
                        def after_receive(self, message_as_dict):
                            logger.debug(f"LoggingDapMessagesListener::after_receive({message_as_dict})")
                        
                        def before_send(self, message_as_dict):
                            logger.debug(f"LoggingDapMessagesListener::before_send({message_as_dict})")  
                    pydevd.add_dap_messages_listener(LoggingDapMessagesListener())
                    
                    #display a "D" button in the quick-access toolbar as a visual indicator to the user that debugging is now active.
                    debugging_started = True
                    addin._simpleFusionCustomCommands.append(SimpleFusionCustomCommand(name="D_indicator", app=app(), logger=logger))
                
                
                
            if debug and script_path:
                debugpy.wait_for_client()
                # to more closely mimic the behavior of Fusion's ui-based debugging button, we should 
                # do this waiting for client in a separate thread, so as not to block the main thread.
                

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
                    logger.fatal(
                        "Unhandled exception while importing and running script.",
                        exc_info=sys.exc_info()
                    )
            

            # i = 0
            # # wait_for_client experiment
            # while i<5:
            #     debugpy.wait_for_client()
            #     # we seem to be iterating on the initial connection (i.e. pressing F5 in VS code)
            #     # and on pressing the restart button in VS code.
            #     # this is good -- this observation is consistent with Fusion using wait_for_client to
            #     # for all interaction with vs code.
            #     # Presumably, when I press F5 in vs code, vs code sends to the debug adapter information
            #     # about which file is active in VS code.  Is this information accessible here?
            #     # Does Fusion's behavior when initiaiting debugging from the UI buttons require 
            #     # Fusion to know which file is active in VS code?  In other words, once we have used
            #     # the Fusion UI buttons to start a script or add-in in debug mode, does Fusion behave any differently in 
            #     # response to a pres of F% in VS code depending on which file is active in VS code.  (My hunch is no.)
            #     # Actually, fusion does seem to know at least the parent directory of the file active in vs code.
            #     # I reckon Fusion must be getting this information from the gloabal PyDB object.

            #     #Based on the messages that I caught with my LoggingDapMessagesListener, it looks like
            #     # the path information the vscode sends to the debug adapter is precisely the information
            #     # defined in the vscode launch.json file -- that makes sense.  But how is it happening that
            #     # fusion runs the add-in/script specified by that path.  Is Fusion doing that, or is Fusion 
            #     # setting up debugpy to do that.  In either case, how?


            #     pydb.block_until_configuration_done

            #     i += 1
            #     logger.debug(f"client connected {i}")
            #     while debugpy.is_client_connected():
            #         pass

            # have to let debugpy.listen() finish before we can attach message listeners (yes, I know
            # that the right way to do this is with a threading.Event(), or do the attaching of the listeners
            # inside debugPyListenerThreadTarget().  Sleeping is just a hack.

            # we have managed to reproduce much of the behavior of the fusion-ui-based launching of add-ins and scripts in debug mode,
            # but one thing we have not been able to reproduce is the behavior where clicking the "reload" button in VS code debugging interface
            # causes the add-in or script to run again.
            #also, we have not reprodfuced the behavior where fusion waits for the ide to connect to the debug adapter before running the 
            # script.  Somehow, we need to inject a wait-for-client function call just before running the script (but in another thread so as not to black
            # fusion's main thread), and somehow we need to catch the client refresh button press and re-launch jthe script in response.

            # perhaps there is something already established between fusion and the gloabl PyDB object such that I do not need
            # to bother running the script here, but rather can rely on this pre-established configuration to run the script merely as a result of
            # hitting F5 in vs code.


        except Exception:
            logger.fatal("An error occurred while attempting to start script.", exc_info=sys.exc_info())
        finally:
            pass

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
 