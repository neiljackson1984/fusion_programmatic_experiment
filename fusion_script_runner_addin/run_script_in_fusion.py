# This script constructs an http request based on the arguments, and sends the request
# to the (assumed to be already-running) fusion_script_runner_addin, assumed ot be already running within
# Fusion. 
# (if we wanted to get fancy, we could try to detect the condition where fusion, or the addin within it,
# are not already running, and then take corrective action).

import sys
import json
import requests
import argparse
import pathlib

##==========================================
##   COLLECT THE PARAMETERS: 
##==========================================

# we probably ought to wrap the meat of this script into a main() function and only run it
# in case this function is being run as a script (As opposed to being iomported as a module),
# but I have not bothered to do this.

DEFAULT_PORT_NUMBER_FOR_HTTP_SERVER = 19812
DEFAULT_DEBUG_PORT_NUMBER = 9000

parser = argparse.ArgumentParser(
    description="""
Send a request to the fusion_script_runner_addin, 
assumed to be already running within Fusion (also assumed to be already 
running) to run a python script or add-in (in roughly the same way 
as would happen if the user were to use the Fusion UI to run the script.
"""
)

parser.add_argument('--script',
    dest='script',
    action='store',
    nargs='?',
    required=True,
    help="the path of the script file that is to be run."
)
# to stay true to the way fusion_script_runner_addin works, we ought to allow
# the user to omit the script argument and specify debug=True,
# because this is a sensible input to the fusion_script_runner_addin (it simply starts the debug server but doesn't run any script)


parser.add_argument('--addin_port',
    dest='addin_port',
    action='store',
    nargs='?',
    required=False,
    # default=str(DEFAULT_PORT_NUMBER_FOR_HTTP_SERVER),
    default=DEFAULT_PORT_NUMBER_FOR_HTTP_SERVER,
    type=int,
    help="the number of the tcp port on which the the fusion_script_runner_addin is listening for http requests."
)
# We could, and probably should, allow the user to specify an arbitrary host and port, to handle cases
# where we do not want to assume implicitly that the host is localhost.


def argStringToBool(x: str) -> bool:
    y = x.strip().lower()
    return ({'false':False, 'true':True}[y] if y in ('false', 'true') else bool(int(y)))

parser.add_argument('--debug',
    dest='debug',
    action='store',
    # action=argparse.BooleanOptionalAction,
    nargs='?',
    required=False,
    default=False,
    const=True,
    type=argStringToBool ,
    help="""
        boolean specifying whether we want to run the script in debug mode.  Debug mode is roughly analagous to the user using the Fusion UI to run a script in debug mode.
    """
)


parser.add_argument('--debug_port',
    dest='debug_port',
    action='store',
    nargs='?',
    required=False,
    default=DEFAULT_DEBUG_PORT_NUMBER,
    type=int,
    help="""
        Specify the number of the port on which you want to have the debug adaptor process 
        (which will be created by the addin) listen for 
        requests from the 'client' (i.e. the IDE, for instance vscode) (not to be confused with the 'debug server' which is a thread running within the 
        'debuggee' (the python environment within Fusion) running pydevd.  The 'debug adaptor' is not well described as either a 'server' or a 'client' --
        although in general the debug adaptor mostly listens on tcp ports rather than initiating new tcp connections, so in that sense
        it might be called a 'server'.
        Only relevant in case dbeug is true.
    """
)
# We could, and probably should, allow the user to specify an arbitrary host and port, to handle cases
# where we do not want to assume implicitly that the host is localhost.


parser.add_argument('--debugpy_path',
    dest='debugpy_path',
    action='store',
    nargs='?',
    required=False, default='',
    help="the path that we must append to sys.path in order to be able to succesfully call 'import debugpy'.  Required only if debug is true."
)
# I do not know (and am not at this moment going to bother to find out) how to set up parser so that debugpy_path
# is required only when debug=True is specified.  For now, we will specify that debugpy_path is not required and 
# then let the program crash and burn in case the user fails to specify it when it is actually needed.


args, unknownArgs = parser.parse_known_args()

if(args.debug):
    # normalize args.debugpy_path
    args.debugpy_path = ( 
        str(pathlib.Path(args.debugpy_path).resolve())
        if args.debugpy_path
        else ''
    )

##==========================================
##   ISSUE THE REQUEST: 
##==========================================

session = requests.Session()



#as originally written, Ben Gruver's add-in expects the 
# post request to be formatted like the following (note how we have to
# serialize the 'message' property.
# response = session.post(
#     f"http://localhost:{PORT_NUMBER_FOR_HTTP_SERVER}",
#     data=json.dumps(
#             {
#             # 'pubkey_modulus':,
#             # 'pubkey_exponent':,
#             # 'signature':,
#             'message':json.dumps({
#                 'script': "foo", # a string - the path of the script file
#                 'debug':  "bar",   # an int, which is interpreted as a boolean.
#                 'pydevd_path': "baz"    # a string
#             })
#         }
#     )
# )

#with my modification, we do not have to (although we can if desired)
# serialize the 'message' property.
# response = session.post(
#     f"http://localhost:{PORT_NUMBER_FOR_HTTP_SERVER}",
#     data=json.dumps(
#             {
#             # 'pubkey_modulus':,
#             # 'pubkey_exponent':,
#             # 'signature':,
#             'message':{
#                 'debug':  True,   # an int or a boolean, or anything which can be cast to an int and then interp[reted as a boolean.
#                 'debug_port': 9000,
#                 'pydevd_path':'C:/Users/Admin/.vscode/extensions/ms-python.python-2021.6.944021595/pythonFiles/lib/python/debugpy/_vendored/pydevd',
#                 'script': "C:/work/fusion_programmatic_experiment/arbitrary_script_1.py" # a string - the path of the script file
                
#                 # # the path that we must add to sys.path in order to be able to succesfully call 'import debugpy'
#                 # 'debugpy_path': "C:/Users/Admin/.vscode/extensions/ms-python.python-2021.6.944021595/pythonFiles/lib/python",    # a string
#             }
#         }
#     )
# )
 
# 


response = session.post(
    f"http://localhost:{args.addin_port}",
    data=json.dumps(
            {
            # 'pubkey_modulus':,
            # 'pubkey_exponent':,
            # 'signature':,
            
            'message':{

                'debug':  
                    # an int or a boolean, or anything which can be cast to an int and then interpreted as a boolean.
                    args.debug, 


                'debug_port':
                    # here, we specify the number of the port on which we want to have the debug adaptor process (which will be created by the addin) listen for 
                    # requests from the 'client' (i.e. the IDE, for instance vscode) (not to be confused with the 'debug server' which is a thread running within the 
                    # 'debuggee' (the python environment within Fusion) running pydevd.  The 'debug adaptor' is not well described as either a 'server' or a 'client' --
                    # although in general the debug adaptor mostly listens on tcp ports rather than initiating new tcp connections, so in that sense
                    # it might be called a 'server'.
                    args.debug_port,

                

                'script': 
                    # a string - the path of the script file
                    args.script, 
                

                'debugpy_path': 
                    # the path that we must add to sys.path in order to be able to succesfully call 'import debugpy'
                    args.debugpy_path,    
            }
        }
    )
)
 





