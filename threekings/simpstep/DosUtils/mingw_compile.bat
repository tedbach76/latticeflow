rem simpdefs
rem make sure that you use pexports to compile the library first.

cd ..
del build 
python setup.py build --compiler=mingw32 bdist_wininst 
cd DosUtils

rem -------------------------------- DEBUG MODULE
rem python setup.py build --compiler=mingw32 --debug bdist_wininst 
