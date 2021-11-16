import os, sys
import adsk.core, adsk.fusion, traceback
import inspect
import pprint
from typing import Optional, Sequence, Union
# from . import scripted_component
from . import bit_holder
# from .scripted_component import ScriptedComponent
# from .bolt import Bolt
from .braids.fscad.src.fscad import fscad as fscad
from .highlight import *
import uuid
import traceback
import time

import pathlib
import itertools

def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent


def renderEntityToken(entityToken: str) -> str:
    # return "\n".join( entityToken.split('/'))
    import base64
    import string
    import zlib
    
    bb = base64.b64decode(entityToken)
    ss = []

    for i in range(len(bb)):
        # try:
        #     s = ba[i:i+1].decode('ascii')
        # except:
        #     s = ba[i:i+1].hex()

        if (
            bb[i] in string.printable.encode('ascii') 
            and not (bb[i] in "\t\r\n\x0b\x0c".encode('ascii'))
            and bb[i] != 255
            and False
        ) :
            s = bb[i:i+1].decode('ascii')
        else:
            s = bb[i:i+1].hex()
        ss.append(s)

    # zlib.decompress(bb[21:])

    return  "".join(ss)
    # + "\n" + "\n".join( 
    #     (
    #         str(len(piece)) + ' ' + piece
    #         for piece in entityToken.split('/')
    #     )
    
    # )
    return entityToken

def run(context:dict):
 
    def design1():
        
        bit_holder.getCannedBitHolders()['1/4-inch hex shank driver bits holder'].create_occurrence()


    #monkeypatching traceback with vscode-compatible link formatting
    initialTracebackStackSummaryFormatMethod = formatStackSummary
    traceback.StackSummary.format = formatStackSummary
    fscad.run_design(design_func=design1, message_box_on_error=False)
    traceback.StackSummary.format = initialTracebackStackSummaryFormatMethod
    # run_design(design_func=design2, message_box_on_error=False)
    # print(traceback.format_tb(sys.last_traceback))

    print(f"finished running {__file__}")

# prevent this module from being terminated when the script returns
# adsk.autoTerminate(False)

def stop(context:dict):
    print(__file__ + " is stopping.")
    pass


#copied, with modification, from the python library function traceback.StackSummary::format()
# we are tweaking the format of the file name and line number information to conform with
# the relatively strict format (filename followed b y a colon followed by the line number) that
# vscode must have in the debug console output in order to automatically create a link
# to zap to the specified line number in the specified file.
def formatStackSummary(stackSummary : traceback.StackSummary) -> Sequence[str]:
    """Format the stack ready for printing.

    Returns a list of strings ready for printing.  Each string in the
    resulting list corresponds to a single frame from the stack.
    Each string ends in a newline; the strings may contain internal
    newlines as well, for those items with source text lines.

    For long sequences of the same frame and line, the first few
    repetitions are shown, followed by a summary line stating the exact
    number of further repetitions.
    """
    result = []
    last_file = None
    last_line = None
    last_name = None
    count = 0
    for frame in stackSummary:
        if (last_file is None or last_file != frame.filename or
            last_line is None or last_line != frame.lineno or
            last_name is None or last_name != frame.name):
            if count > traceback._RECURSIVE_CUTOFF:
                count -= traceback._RECURSIVE_CUTOFF
                result.append(
                    f'  [Previous line repeated {count} more '
                    f'time{"s" if count > 1 else ""}]\n'
                )
            last_file = frame.filename
            last_line = frame.lineno
            last_name = frame.name
            count = 0
        count += 1
        if count > traceback._RECURSIVE_CUTOFF:
            continue
        row = []
        # row.append('  File "{}", line {}, in {}\n'.format(
        row.append('  File "{}:{}" in {}\n'.format(
            frame.filename, frame.lineno, frame.name))
        if frame.line:
            row.append('    {}\n'.format(frame.line.strip()))
        if frame.locals:
            for name, value in sorted(frame.locals.items()):
                row.append('    {name} = {value}\n'.format(name=name, value=value))
        result.append(''.join(row))
    if count > traceback._RECURSIVE_CUTOFF:
        count -= traceback._RECURSIVE_CUTOFF
        result.append(
            f'  [Previous line repeated {count} more '
            f'time{"s" if count > 1 else ""}]\n'
        )
    return result

#monkeypatching traceback with vscode-compatible link formatting
traceback.StackSummary.format = formatStackSummary