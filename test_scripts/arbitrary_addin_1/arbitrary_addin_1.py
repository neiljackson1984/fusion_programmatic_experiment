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
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent.resolve()))
from simple_fusion_custom_command import SimpleFusionCustomCommand



# from rpyc.core import SlaveService
# from rpyc.lib import setup_logger
# from rpyc.utils.server import Server, ThreadedServer, ForkingServer, OneShotServer 


NAME_OF_THIS_ADDIN = 'arbitrary_addin_1'
ERROR_DIALOG_EVENT_ID = f"{NAME_OF_THIS_ADDIN}_error_dialog"

def app() -> adsk.core.Application: return adsk.core.Application.get()
def ui() -> adsk.core.UserInterface: return app().userInterface

logger = logging.getLogger(NAME_OF_THIS_ADDIN)
logger.propagate = False

class AddIn(object):
    def __init__(self):
        self._error_dialog_event_handler            : Optional[ErrorDialogEventHandler]         = None
        self._error_dialog_event                    : Optional[adsk.core.CustomEvent]           = None
        self._logging_file_handler                  : Optional[logging.Handler]                 = None
        self._logging_dialog_handler                : Optional[logging.Handler]                 = None
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
            self._simpleFusionCustomCommands.append(
                SimpleFusionCustomCommand(
                    name="arbitrary_add_in_1_command", 
                    app=app(), 
                    logger=logger,
                    action=(lambda eventArgs: ui().palettes.itemById('TextCommands').writeText(str(datetime.datetime.now()) + "\t" + 'Hello from ' + __file__))
                )
            )

        except Exception:
            logger.fatal(f"Error while starting {NAME_OF_THIS_ADDIN}", exc_info=sys.exc_info())

    
    def stop(self):
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


class ErrorDialogEventHandler(adsk.core.CustomEventHandler):
    """An event handler that shows an error dialog to the user."""
    def notify(self, args):
        ui().messageBox(args.additionalInfo, f"{NAME_OF_THIS_ADDIN} error")


class FusionErrorDialogLoggingHandler(logging.Handler):
    """A logging handler that shows a error dialog to the user in Fusion 360."""
    def emit(self, record: logging.LogRecord) -> None:
        adsk.core.Application.get().fireCustomEvent(ERROR_DIALOG_EVENT_ID, self.format(record))


addin = AddIn()

def run(context:dict):
    addin.start()

def stop(context:dict):
    logger.debug("stopping")
    addin.stop()
 