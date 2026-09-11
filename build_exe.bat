@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=py"

"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean BlueArchive_axiseditor.spec
if errorlevel 1 (
  echo.
  echo Build failed. Install dependencies with:
  echo py -3 -m pip install -r requirements.txt PyInstaller
  pause
  exit /b 1
)

echo.
echo Done: dist\BlueArchive_axiseditor.exe
exit /b 0
