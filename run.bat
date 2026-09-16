@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ======================================
echo          StudyOS - Local Launcher
echo ======================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

%PY% --version >nul 2>nul
if errorlevel 1 goto :python_error

if not exist "venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment...
  %PY% -m venv venv
  if errorlevel 1 goto :error
) else echo [1/4] Virtual environment found.

echo [2/4] Installing dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :network_error

echo [3/4] Checking project and preparing database...
venv\Scripts\python.exe manage.py check
if errorlevel 1 goto :error
venv\Scripts\python.exe manage.py migrate --noinput
if errorlevel 1 goto :error

echo [4/4] Starting StudyOS...
echo.
echo Open http://127.0.0.1:8000/ in your browser.
echo Keep this window open while using StudyOS.
echo Press Ctrl+C to stop the server.
echo.
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
exit /b %errorlevel%

:python_error
echo Python is not installed or is not available as "py" or "python".
echo Install Python 3.11+ and run this file again.
pause
exit /b 1

:network_error
echo.
echo Dependencies could not be installed.
echo Check your internet connection and try again.
pause
exit /b 1

:error
echo.
echo StudyOS setup/check failed. Read the error above.
pause
exit /b 1
