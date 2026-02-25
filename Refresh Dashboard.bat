@echo off
echo Refreshing Blockchain Dashboard...
"C:\Users\ROB8341\AppData\Local\anaconda3\python.exe" "%~dp0generate_dashboard.py"
if %errorlevel% equ 0 (
    echo Dashboard updated successfully!
    start "" "%~dp0blockchain_dashboard.html"
) else (
    echo Error generating dashboard. Press any key to close.
    pause >nul
)
