rem Useful path settings for compiling SIMP. Edit as necessary
rem To source it, type simp from the command line

rem ---- EDIT THESE VARIABLES IF NECESSARY
rem Set the Python version you want to use
set PYVER=24
rem Path to the python dll file 
rem on WIN XP and such
set PYDLLPATH=C:\windows\system32
rem on older versions of windows (uncomment if necessary)
rem set PYDLLPATH=C:\windows\system


rem ---- SCRIPT--- Don't edit
rem Set up paths
set PYPATH=C:\Python%PYVER%\
set MINGWPATH=C:\mingw\bin\
set PATH=%PYPATH%;%MINGWPATH%;%PATH%
rem point to the PYTHON DLL
set PYDLL=python%PYVER%.dll
set PYDLLFILE=%PYDLLPATH%\%PYDLL%



