@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:python_fallback
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
goto launch
:run
".venv\Scripts\python.exe" -c "import PySide6, pyqtgraph, numpy" >nul 2>nul
if errorlevel 1 goto install
:launch
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo HAL2030 could not start. Use Python 3.11-3.14 and check the error above.
echo First-time dependency installation requires internet access.
pause
exit /b 1
