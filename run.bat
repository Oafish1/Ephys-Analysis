@ECHO OFF
call activate ephys
:start
python notebook_setup.py
GOTO start
