@echo off
setlocal
where py.exe >nul 2>nul
if not errorlevel 1 (
    py.exe -3 "%~dp0foreground_logger.py" --stop
    if errorlevel 1 pause
    exit /b
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python.exe "%~dp0foreground_logger.py" --stop
    if errorlevel 1 pause
    exit /b
)
echo Python was not found. Install Python 3 with the launcher or add it to PATH.
pause
exit /b 1
