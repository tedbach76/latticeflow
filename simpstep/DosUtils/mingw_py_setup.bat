rem Set the location of python and windows
rem !!!! Must run simpdefs first !!!!

rem  | copy the python dll here:
rem  |    For some odd reason, either pexports or dlltool need to be in the 
rem  |    same directory as the dll.  Specifying a path like 
rem  |    "c:/windows/system32" makes the compiled version think that the 
rem  |    dll file is called "cwindowssystem32python23.dll"
copy %PYDLLFILE% .
copy %PYDLLFILE% .


rem -------------------------------- create libpython??.a
rem ---------------- CALL PEXPORTS and DLLTOOL 
pexports %PYDLL%  > python.def 
dlltool  --dllname %PYDLL% --def python.def --output-lib %PYPATH%libs\libpython%PYVER%.a
rem -------------------------------- create fake debug file, libpython??_d.a
copy %PYPATH%libs\libpython%PYVER%.a %PYPATH%libs\libpython%PYVER%_d.a 