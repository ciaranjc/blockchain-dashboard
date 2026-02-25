@echo off
echo Refreshing Blockchain Dashboard...
echo.

cd /d "%~dp0"
set DUNE_API_KEY=RFMOcmSflJvpo2iYn40WMETlR9cN58pm
python generate_dashboard.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Something went wrong. See message above.
    pause
) else (
    echo.
    echo Done! Opening dashboard...
    start "" "blockchain_dashboard.html"
    timeout /t 3 >nul
)
