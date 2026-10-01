@echo off
setlocal
where pyw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pyw.exe -3 "%~dp0foreground_logger.py"
    exit /b
)
where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%~dp0foreground_logger.py"
    exit /b
)
echo Python was not found. Install Python 3 with the launcher or add it to PATH.
pause
exit /b 1
