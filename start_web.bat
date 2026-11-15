@echo off
setlocal
cd /d "%~dp0"

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

if exist ".venv\Scripts\python.exe" goto check_deps

echo Creating virtual environment (.venv)...
where py >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install

:python_fallback
python -m venv .venv
if errorlevel 1 goto failed

:install
echo Installing dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
goto launch

:check_deps
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, numpy, pandas, scipy" >nul 2>nul
if errorlevel 1 goto install

:launch
echo.
echo Starting ASTRA-Core Web Console on http://127.0.0.1:%PORT% ...
echo Press Ctrl+C in this window to stop the server.
echo.

REM Wait in background until the server responds, then open the browser
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for ($i=0; $i -lt 30; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%PORT%/' -TimeoutSec 1; if ($r.StatusCode -eq 200) { Start-Process 'http://127.0.0.1:%PORT%'; break } } catch {}; Start-Sleep -Milliseconds 500 }"

".venv\Scripts\python.exe" -m uvicorn server:app --host 127.0.0.1 --port %PORT%
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo ASTRA-Core Web Console could not start. Use Python 3.11-3.14 and check the error above.
echo First-time dependency installation requires internet access.
pause
exit /b 1
