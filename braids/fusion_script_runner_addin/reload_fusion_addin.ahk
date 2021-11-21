; This is an keystroke-sending-based way to reload a fusion add-in.
; Useful during debugging of an add-in.


#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetKeyDelay 20
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
DetectHiddenWindows, On
SetTitleMatchMode, 1
#singleInstance force

; this script reads the first non-option argument (i.e. an argument not starting with "-" or "/"),
; which it takes to be the name of a fusion add-in (Assumed to be already in fusion's list of add-ins).
;Then, we send keystrokes to fusion to (hopefully reload the add-in)
; to-do: add debugging flag

; the script looks for the --debug flag, and, if present, attempts to reload the 
; specified add-in in debugging mode
; NOT YET IMPLEMENTED
debug:=GetSwitchParams("((--debug))")

; TODO: allow user to specify whether this is a 'script' or an 'add-in'

GetParams("nonSwitchParameters")

nameOfAddin:=nonSwitchParameters1
; MsgBox, %nameOfAddin%

;Get the currently active window  
WinGet, originalActiveWindow, ID, A

WinGet, fusionMainWindowHandle, ID, Autodesk Fusion 360 ahk_exe Fusion360.exe

if (fusionMainWindowHandle == "")
{
	MsgBox, "Fusion360 needs to be running for this script to work. Please start Fusion360 and try again."
	ExitApp
}
WinActivate, ahk_id %fusionMainWindowHandle%
Sleep, 100

;;cancel any running command:
Send {Esc}{Esc}
Sleep, 100
;; send shift-s to open the "Scripts and Add-Ins" dialog:
Send +s

Sleep, 250
; at this point, if everything has gone according to plan, the Scripts and Add-Ins window should be
; freshly opened.
WinGet, fusionScriptsAndAddinsWindowHandle, ID, Scripts and Add-Ins ahk_exe Fusion360.exe
if (fusionScriptsAndAddinsWindowHandle == "")
{
	MsgBox, "We have failed to open Fusion's 'Scripts and Add-Ins" dialog, and therefore cannot proceed."
	ExitApp
}


;;Send ctrl-Tab to switch to the add-ins tab
Send ^{Tab}

;;send tab to activate the the add-ins list
Send {Tab}
Sleep, 50
;; Type the name of the add-in, which should cause the specified add-in to become selected
SendRaw %nameOfAddin%

; send three tabs, whcih will activate the "stop" button if the add-in is already running,
; or the "run" button is the add-in is not already running
Send {Tab}{Tab}{Tab}

; send a space to click the button that we have selected
Send {Space}
Sleep, 600
; if the add-in was not ruinning initially, then we wil have just clicked the "Run" button, which will
; have caused the add-in to start and will have closed the "Scripts and Add-Ins" dialog.

; if the add-in was running initially, then we will have just clicked the "Stop" button, which will
; have caused the add-in to stop, but will not have closed the "Scripts and Add-Ins" dialog.  
; In this case, we should now send shift-tab to select the run button, then space to click it.
; Hopefully the shift-tab and space keystrokes will have no effect in the case where the add-in was not initially running because the 
; Scripts and Add-Ins window will have disappeared.


; test whether the scripts and add-ins window is still present.
WinGet, fusionScriptsAndAddinsWindowHandle, ID, Scripts and Add-Ins ahk_exe Fusion360.exe
if (fusionScriptsAndAddinsWindowHandle != "")
{
	; In this case, the scripts and add-ins window is still present, which means that 
	; the add-in must have been initially running, and we just clicked the stop button to stop it.
	; send shift-tab to select the run button, then space to click it.
	Send +{Tab}
	Send {Space}
} 


Sleep, 120
WinActivate, ahk_id %originalActiveWindow%




















; from https://autohotkey.com/board/topic/46924-parameters-and-switches-parser/ :
;;;   /*
;;;   NbParams := GetParams(ParamArrayName[, MaxParams = ""]) 
;;;   
;;;   Retrieves the non-switch-parameters (i.e the parameters not starting 
;;;   with a '-' or a '/') into an array : 
;;;   
;;;   ParamArrayName : string or variable containing a string that will be 
;;;   used as a prefix for an array containing the parameters : 
;;;   %ParamArrayName%1 contains 1st param, %ParamArrayName%2 contains 2nd, 
;;;   etc. %ParamArrayName%0 will contain the number of items found. MaxParams 
;;;   : the maximum number of parameters that should be saved into the array. 
;;;   
;;;   returns : the number of parameters found (same as %ParamArrayName%0) 
;;;   
;;;   NbSubparams := GetSwitch(Switch[, CaseSens = 0, SubparamArrayName = "", 
;;;   MaxSubparams = "", FistParseChar = ":", ParseChar = ""]) 
;;;   
;;;   Detects a switch and optionally retrieve its subparameters (e.g. 
;;;   /sw1:SubParam1:SubParam2) into an array : 
;;;   
;;;   Switch : name of the switch (without - or / prefix), can be a 
;;;   Perl-compatible regular expression (PCRE) WITHOUT pattern options. 
;;;   CaseSens : Set this to 1 if you want the switch detection to be case 
;;;   sensitive SubparamArrayName : string or variable containing a string 
;;;   that will be used as a prefix for an array containing the subparameters 
;;;   : %SubparamArrayName%1 contains 1st param, %SubparamArrayName%2 contains 
;;;   2nd, etc. %SubparamArrayName%0 will contain the number of items found. 
;;;   MaxSubparams : the maximum number of sub parameters that should be saved 
;;;   into the array. If set to -1, the whole string of sub parameters will be 
;;;   retrieved. FirstParseChar : The character separating the switch from its 
;;;   sub params. Default is ":". It can be empty. ParseChar : The character 
;;;   between two sub params. By default, it is set to empty and internally 
;;;   resolves to ":" and will retrieve correctly the paths (e.g "c:\program 
;;;   files" won't be split into "c" and "\program file"). If explicitly set 
;;;   to ":" or any other char, the paths will be split as well. 
;;;   
;;;   returns : 0 if the switch was not found ; -1 if the switch was found but 
;;;   no parameters ; the number of subparameters found (same as 
;;;   %SubparamArrayName%0) 
;;;   
;;;   The parameters passed to the script must match the following rules : 
;;;   
;;;   Non-switch-parameters, e.g. file paths, must be enclosed in quotes if 
;;;   they contain spaces. They will be saved in the order in which they 
;;;   appear. Switches can be placed before, inbetween or after the 
;;;   non-switch-parameters, their order doesn't matter. Switches can be 
;;;   indicated either with '-' or '/'. their subparameters must be separated 
;;;   by ':' Example : /i /time:5:10 -date:11:08:2009 File paths will be 
;;;   parsed correctly even if they contain DRIVELETTER:\ pattern Example : 
;;;   /WorkingDir:M:\Documents\ If a parameter contains spaces, the spaces 
;;;   must be enclosed in quotes Example : /AHKDir:"C:\Program 
;;;   Files\AutoHotkey\" OR /AHKDir:C:\Program" "Files\AutoHotkey\ 
;;;   
;;;   
;;;   */



GetParams(ParamArrayName, MaxParams = "")
{
	Local Params
	Params = 1
	Loop, %0%
	{
		If RegExMatch(%A_Index%, "S)(?:^[^-/].*)", %ParamArrayName%%Params%)
			Params++
		If ((MaxParams != "") && (Params > MaxParams))
			Break
	}
	Params--
	%ParamArrayName%0 := Params
	Return %Params%
}

GetSwitchParams(SwitchName, CaseSens = 0, ParamArrayName = "", MaxParams = "", FirstParseChar = ":", ParseChar = "")
{
	Local Params, Params1, ParseMode
	Static ParamList
	If !ParamList ;Initializing a variable containing all the parameters passed to the script
	{
		Loop, %0%
			ParamList .= "`n" %A_Index%
		ParamList .= "`n"
	}
	If FirstParseChar
		FirstParseChar := ( InStr("\.*?+[{|()^$", SubStr(FirstParseChar, 1, 1)) ? "\" SubStr(FirstParseChar, 1, 1) : SubStr(FirstParseChar, 1, 1) )
	If (ParamArrayName = "") ;if the switch does not require parameters
	{
		If RegExMatch(ParamList, ( CaseSens ? "\n[-/]" SwitchName "(?:\n|" FirstParseChar "\n)" : "i)\n[-/]" SwitchName "(?:\n|" FirstParseChar "\n)"))
			Return -1
		Else
			Return 0
	}
	If (MaxParams = -1) ;the whole content is extracted
	{
		If RegExMatch(ParamList, ( CaseSens ? "\n[-/]" SwitchName "(?:\n|" FirstParseChar "([^\n]*))" : "i)\n[-/]" SwitchName "(?:\n|" FirstParseChar "([^\n]*))" ), %ParamArrayName%)
		{
			%ParamArrayName%0 = 1
			Return 1
		}
		Else
		{
			%ParamArrayName%0 = 0
			Return 0
		}
	}
	If (ParseChar = "")
	{
		ParseChar := ":"
		ParseMode := -2 ;test for files
	}
	Else
	{
		ParseChar := ( InStr("\.*?+[{|()^$", SubStr(ParseChar, 1, 1)) ? "\" SubStr(ParseChar, 1, 1) : SubStr(ParseChar, 1, 1) )
		ParseMode := -3 ;don't test for files
	}
	If RegExMatch(ParamList, ( CaseSens ? "\n[-/]" SwitchName "(?:\n|" FirstParseChar "([^" ParseChar "\n]*(" ParseChar "[^" ParseChar "\n]*)*))" : "i)\n[-/]" SwitchName "(?:\n|" FirstParseChar "([^" ParseChar "\n]*(" ParseChar "[^" ParseChar "\n]*)*))" ) , Params )
	{
		If !(Params1)
		{
			%ParamArrayName%0 = 0
			Return -1 ;switch found but no subparams
		}
		Params = 0
		Loop, Parse, Params1, % ( SubStr(ParseChar, 1, 1) = "\" ?  SubStr(ParseChar, 2) : ParseChar )
		{
			Params++
			If ((ParseMode = -2) && RegExMatch(A_LoopField, "^\\")) ;Managing paths containing LETTER:\..., as they will otherwise be parsed at ":"
			{
				Params--
				If RegExMatch(%ParamArrayName%%Params%, "^[A-Za-z]$")
					%ParamArrayName%%Params% .= ":" A_LoopField
				Else If ((MaxParams != "") && (Params >= MaxParams))
					Break
				Else
				{
					Params++
					%ParamArrayName%%Params% := A_LoopField
				}
			}
			Else If ((MaxParams != "") && (Params > MaxParams))
			{
				Params--
				Break
			}
			Else
				%ParamArrayName%%Params% := A_LoopField
		}
		%ParamArrayName%0 := Params
		Return %Params%
	}
	Else
		Return 0
}


