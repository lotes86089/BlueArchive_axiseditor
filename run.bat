@echo off
setlocal
cd /d "%~dp0"

py -3 -c "import tkinter, PIL" >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
    goto :check_result
)

python -c "import tkinter, PIL" >nul 2>nul
if %errorlevel%==0 (
    python app.py
    goto :check_result
)

set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PYTHON%" (
    "%BUNDLED_PYTHON%" app.py
    goto :check_result
)

echo.
echo Python 3 was not found.
echo Install Python 3 with Tkinter and Pillow, then run this file again.
pause
exit /b 1

:check_result
if errorlevel 1 (
    echo.
    echo The application could not start. See the error above.
    pause
)
endlocal
