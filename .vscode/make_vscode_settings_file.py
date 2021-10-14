"""Programmatically determines the path of the fusion executable and the path of
the debugpy executable (both of which tend to change as a result of fusion and
vscode, respectively, automatically updating themselves), and inject these paths
in the appropriate place in the vscode settings file."""


import sys
import os
import re
import pathlib
import json
import datetime

# this is borrowed from a python script that is included in fusion.
def locatePythonToolFolder():

    vscodeExtensionPath = ''
    if sys.platform.startswith('win'):
        vscodeExtensionPath = os.path.expandvars(r'%USERPROFILE%\.vscode\extensions')
    else:
        vscodeExtensionPath = os.path.expanduser('~/.vscode/extensions')

    if os.path.exists(vscodeExtensionPath) == False:
        return ''

    msPythons = []
    versionPattern = re.compile(r'ms-python.python-(?P<major>\d+).(?P<minor>\d+).(?P<patch>\d+)')
    for entry in os.scandir(vscodeExtensionPath):
        if entry.is_dir(follow_symlinks=False):
            match = versionPattern.match(entry.name)
            if match:
                try:
                    version = tuple(int(match[key]) for key in ('major', 'minor', 'patch'))
                    msPythons.append((entry, version))
                except:
                    pass

    msPythons.sort(key=lambda pair: pair[1], reverse=True)
    if (msPythons):
        if None == msPythons[0]:
            return ''
        msPythonPath = os.path.expandvars(msPythons[0][0].path)
        index = msPythonPath.rfind('.')
        version  = int(msPythonPath[index+1:])
        msPythonPath = os.path.join(msPythonPath, 'pythonFiles', 'lib','python')
        msPythonPath = os.path.normpath(msPythonPath)
        if os.path.exists(msPythonPath) and os.path.isdir(msPythonPath):
            return msPythonPath
    return ''



def getPathOfFusionExecutable() -> str:
    # the strategy is to look at each subfolder of %localappdata%/Autodesk//webdeploy/production .
    # for each we collect the path of the "Fusion360.exe" contained within, if such a file exists.
    # we return the Fusion360.exe file having the most recent timestamp.
    pathOfProductionFolder = pathlib.Path(os.environ['LOCALAPPDATA']).joinpath('Autodesk').joinpath('webdeploy').joinpath('production')
    pathOfFusionExecutable = sorted(
        filter(
            lambda x: x.is_file(),
            (
                pathOfDirectory.joinpath('Fusion360.exe')
                for pathOfDirectory in filter(lambda x: x.is_dir(), pathOfProductionFolder.iterdir())
            )
        ),
        key = lambda x: x.stat().st_ctime
    )[-1]
    return str(pathOfFusionExecutable.resolve())



pathOfVscodeSettingsFile = pathlib.Path(__file__).parent.joinpath('settings.json')
print(f"Now generating (and overwriting) {pathOfVscodeSettingsFile}")



debugpyPath = pathlib.Path(locatePythonToolFolder()).as_posix()
pathOfFusionInstallDirectory = pathlib.Path(getPathOfFusionExecutable()).parent.resolve().as_posix()



print(f"debugpyPath: {debugpyPath}")
print(f"pathOfFusionInstallDirectory: {pathOfFusionInstallDirectory}")

vscodeSettings = {
    "neil.debugpyPath": debugpyPath,
    "neil.pathOfFusionInstallDirectory": pathOfFusionInstallDirectory,

    "python.autoComplete.extraPaths":	[
		"C:/Users/Admin/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Python/defs",
		
		# it does not seem to work to define one setting value in terms of another, unfortunately.
		# "${config:neil.debugpyPath}",
		# "${config:neil.debugpyPath}/debugpy/_vendored/pydevd",
		f"{debugpyPath}",
		f"{debugpyPath}/debugpy/_vendored/pydevd",
		"./fusion_script_runner_addin",
		"./lib",
		"./braids/fscad/src/fscad",
		"./braids/fscad/src",
		"."
	],
	"python.pythonPath":	f"{pathOfFusionInstallDirectory}/Python/python.exe",
	"python.linting.pylintEnabled": False,
	"python.analysis.extraPaths": [
		"C:/Users/Admin/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Python/defs",
		f"{debugpyPath}",
		f"{debugpyPath}/debugpy/_vendored/pydevd",
		"./fusion_script_runner_addin",
		"./lib",
		"./braids/fscad/src/fscad",
		"./braids/fscad/src",
		"C:/work/lalboard",
		"."
	],
	"VsCodeTaskButtons.tasks": [ 
			{"label":"restart_fusion" , "task":"restart_fusion"}
	],

    "terminal.integrated.profiles.windows": {
        "Command Prompt": {
            "path": [
                "${env:windir}\\Sysnative\\cmd.exe",
                "${env:windir}\\System32\\cmd.exe"
            ],
            "args": [],
            "icon": "terminal-cmd"
        }
    },

	# https://stackoverflow.com/questions/69047142/vscode-is-suddenly-defaulting-to-powershell-for-integrated-terminal-and-tasks?noredirect=1
	"terminal.integrated.defaultProfile.windows": "Command Prompt",
	"terminal.integrated.automationShell.windows": "cmd.exe"
	 
}


import textwrap
with open(pathOfVscodeSettingsFile, 'w') as vscodeSettingsFile:
    lineWidth = 80
    messageParagraphs = [
        f"DO NOT EDIT THIS FILE MANUALLY.",
        f"THIS VSCODE SETTINGS FILE HAS BEEN GENERATED PROGRAMMATICALLY BY {__file__}.",
        f"CREATED {datetime.datetime.now()}"
    ]

    formattedBoxedMessage = "\n".join(
        [
            "/**" + "*"*( lineWidth - 6) + "** ",
            *[
                " * " + ( line + " "*(lineWidth - 6 - len(line)) ) +  " * "
                for paragraph in messageParagraphs
                for line in textwrap.wrap(paragraph, width=lineWidth - 6) + [""]
            ],
            "***" + "*"*( lineWidth - 6) + "**/"
        ]
    )
    vscodeSettingsFile.write(formattedBoxedMessage + "\n\n\n")

    json.dump(vscodeSettings, vscodeSettingsFile, indent=4)