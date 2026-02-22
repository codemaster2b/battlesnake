start cmd.exe /k py %~dp0help_run1.py %~n0
timeout /t 3 /nobreak > NUL
start cmd.exe /k py %~dp0help_run2.py %~n0
