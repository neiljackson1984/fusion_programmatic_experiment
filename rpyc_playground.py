# This script is meant to talk, via RPyC, to the already-runninng add-in loaded into Fusion 360.

import sys
sys.path.append('C:/Users/Admin/AppData/Local/Autodesk/webdeploy/production/48ac19808c8c18863dd6034eee218407ecc49825/Api/Python/packages')

import rpyc
import pathlib
import rpyc.core.service
import json
import adsk.core, adsk.fusion, traceback
import requests

PORT_NUMBER_FOR_RPYC_SLAVE_SERVER = 18812
PORT_NUMBER_FOR_HTTP_SERVER = 19812


print("XXXXXXXXXXXX")
conn = rpyc.classic.connect("localhost", port=PORT_NUMBER_FOR_RPYC_SLAVE_SERVER)
print("Hello World!", file=conn.modules.sys.stdout)


script='''

message=""
message += str(dir())


'''

conn.execute(script)
print(conn.eval('message'))

exit()










print("conn.modules: " + str(conn.modules))
print("conn.namespace: " + str(conn.namespace))
# remoteBuiltins = conn.modules['builtins']
# print("dir(conn.builtins): " + "\n" + "\n".join(dir(conn.builtins)) + "\n")
print("dir(conn.modules): " + "\n" + "\n".join(dir(conn.modules)) + "\n")
# print("conn.modules: " + "\n" + "\n".join(conn.modules) + "\n")


# print("dir(conn.builtins.globals): " + str(dir(conn.builtins.globals)))
# print("dir(conn.builtins.locals): " + str(dir(conn.builtins.locals)))
print("conn.root: " + str(conn.root))


conn.execute('import adsk.core, adsk.fusion, traceback')
rapp :adsk.core.Application = conn.eval('adsk.core.Application.get()')
# rapp  = conn.eval('adsk.core.Application.get()')
# rapp.userInterface.messageBox('Hello addin')

 
rsys = conn.modules['sys']
ros = conn.modules['os']
# rdebugpy = conn.modules['debugpy']f
print("rsys.path: " + "\n" + "\n".join(rsys.path) + "\n")
# exit(0)
rmodules = rsys.modules
# print("rmodules.keys(): " + str(rmodules.keys()))


report = "rsys.modules: " + "\n"

for k in rmodules:
    report += k + " "
    try:
        report += rmodules[k].__file__
    except Exception as e:
        # report += str(e)
        report += "oops"
    report += "\n"

print(report)



# print("dir(rsys.modules['neutronSupport']): " + "\n" + "\n".join(dir(rsys.modules['neutronSupport']))  + "\n")
# print("dir(rsys.modules['neu_internal']): " + "\n" + "\n".join(dir(rsys.modules['neu_internal']))  + "\n")


# print("rdebugpy: " + str(rdebugpy))
# conn.execute('import runpy')
# rrunpy = conn.modules['runpy']
# print("rrunpy: " + str(rrunpy))
print("conn.eval('__name__'): " + conn.eval('__name__'))
print("ros.getcwd(): " + ros.getcwd())
# conn.builtins.exit()

# rdebugpy.listen(9000)

# rrunpy.run_path(pathOfTheArbitraryScript)

# rapp.fireCustomEvent(
#     'scriptRunRequested_customEvent', 
#     json.dumps({
#         'action':'runScript',
#         'arguments':{
#             'pathOfScript': str(pathOfTheArbitraryScript),
#             'debugMode': True
#         }
#     })
# )
# for workspace in rapp.userInterface.workspaces:
#     workspace = adsk.core.Workspace.cast(workspace)
#     print('workspace.name: ' + workspace.name)
#     print('workspace.resourceFolder: ' + workspace.resourceFolder)
#     print('')
# # print('rapp.userInterface.activeWorkspace.resourceFolder: ' + rapp.userInterface.activeWorkspace.resourceFolder)



if conn.modules.__contains__('pydevd'):
    rpydevd = conn.modules['pydevd']
    print("rpydevd.__file__: " + rpydevd.__file__)
    rpydb = conn.modules['pydevd'].get_global_debugger()
    print("dir(rpydb): " + "\n" + "\n".join(dir(rpydb)))
    print("rpydb._dap_messages_listeners: " + "\n" + "\n".join(map(str,rpydb._dap_messages_listeners)))
    print("rpydb.plugin: " + str(rpydb.plugin))
    conn.execute('import sys')
    print("pydb.__module__: " + conn.eval('sys.modules["pydevd"].get_global_debugger().__module__'))
    print("rpydb._cmd_queue: " + str(rpydb._cmd_queue))
    print("rpydb._cmd_queue['*']: " + str(rpydb._cmd_queue['*']))
    print("dir(rpydb._cmd_queue['*']): " + "\n" + "\n".join(dir(rpydb._cmd_queue['*'])))
    print("rpydb._cmd_queue['*'].unfinished_tasks: " + str(rpydb._cmd_queue['*'].unfinished_tasks))
    # print("rpydb._cmd_queue['*'].get(): " + str(rpydb._cmd_queue['*'].get()))
    print("dir(rpydb._files_filtering): " + "\n" + "\n".join(dir(rpydb._files_filtering)))
    print("rpydb._files_filtering._get_project_roots(): " + "\n" + "\n".join(rpydb._files_filtering._get_project_roots()))
    print("conn.modules['pydevd_file_utils'].map_file_to_client('.'): " + str(conn.modules['pydevd_file_utils'].map_file_to_client('.')))
    print("rpydb.source_mapping: " + str(rpydb.source_mapping))
    print("rpydb.source_mapping._mappings_to_server: " + str(rpydb.source_mapping._mappings_to_server))
    print("rpydb.source_mapping._mappings_to_client: " + str(rpydb.source_mapping._mappings_to_client))






pathOfTheArbitraryScript=pathlib.Path(__file__).parent.joinpath('test_scripts').joinpath('arbitrary_script_1').joinpath("arbitrary_script_1.py").resolve()
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
    f"http://localhost:{PORT_NUMBER_FOR_HTTP_SERVER}",
    data=json.dumps(
            {
            # 'pubkey_modulus':,
            # 'pubkey_exponent':,
            # 'signature':,
            'message':{
                'debug':  True,   # an int or a boolean, or anything which can be cast to an int and then interp[reted as a boolean.
                'debug_port': 9000,
                # 'pydevd_path':'C:/Users/Admin/.vscode/extensions/ms-python.python-2021.6.944021595/pythonFiles/lib/python/debugpy/_vendored/pydevd',
                'script': str(pathOfTheArbitraryScript), # a string - the path of the script file
                
                # # the path that we must add to sys.path in order to be able to succesfully call 'import debugpy'
                'debugpy_path': "C:/Users/Admin/.vscode/extensions/ms-python.python-2021.6.944021595/pythonFiles/lib/python",    # a string
            }
        }
    )
)
 
# 
 