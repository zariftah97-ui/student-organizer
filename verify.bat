@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Run run.bat first so dependencies are installed.
  pause
  exit /b 1
)
echo Running Django checks...
venv\Scripts\python.exe manage.py check
if errorlevel 1 goto fail
echo Running test suite...
venv\Scripts\python.exe manage.py test
if errorlevel 1 goto fail
echo.
echo ALL CHECKS PASSED.
pause
exit /b 0
:fail
echo.
echo CHECKS FAILED. Read the error above.
pause
exit /b 1
