# This script is meant to talk, via RPyC, to the already-runninng add-in loaded into Fusion 360.

import sys
sys.path.append('C:/Users/Admin/AppData/Local/Autodesk/webdeploy/production/48ac19808c8c18863dd6034eee218407ecc49825/Api/Python/packages')

import rpyc
import pathlib
import rpyc.core.service
import json
import adsk.core, adsk.fusion, traceback

print("XXXXXXXXXXXX")
conn = rpyc.classic.connect("localhost")
print("Hello World!", file=conn.modules.sys.stdout)
print("conn.modules: " + str(conn.modules))
print("conn.namespace: " + str(conn.namespace))
# remoteBuiltins = conn.modules['builtins']
# print("dir(conn.builtins): " + "\n" + "\n".join(dir(conn.builtins)) + "\n")
print("dir(conn.modules): " + "\n" + "\n".join(dir(conn.modules)) + "\n")


# print("dir(conn.builtins.globals): " + str(dir(conn.builtins.globals)))
# print("dir(conn.builtins.locals): " + str(dir(conn.builtins.locals)))
print("conn.root: " + str(conn.root))


conn.execute('import adsk.core, adsk.fusion, traceback')
rapp :adsk.core.Application = conn.eval('adsk.core.Application.get()')
# rapp  = conn.eval('adsk.core.Application.get()')
# rapp.userInterface.messageBox('Hello addin')


rsys = conn.modules['sys']
rdebugpy = conn.modules['debugpy']
print("rsys.path: " + "\n" + "\n".join(rsys.path) + "\n")
print("rdebugpy: " + str(rdebugpy))
conn.execute('import runpy')
rrunpy = conn.modules['runpy']
print("rrunpy: " + str(rrunpy))
# conn.builtins.exit()

# rdebugpy.listen(9000)
pathOfTheArbitraryScript=pathlib.Path(__file__).parent.joinpath("arbitrary_script_1.py").resolve()
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
for workspace in rapp.userInterface.workspaces:
    workspace = adsk.core.Workspace.cast(workspace)
    print('workspace.name: ' + workspace.name)
    print('workspace.resourceFolder: ' + workspace.resourceFolder)
    print('')
# print('rapp.userInterface.activeWorkspace.resourceFolder: ' + rapp.userInterface.activeWorkspace.resourceFolder)

# 
