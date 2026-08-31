@echo off
title P2P Crypto Bot & GoPay Gateway Full Stack Launcher
cd /d "%~dp0"

echo ===================================================
echo   P2P Crypto Bot & GoPay Gateway Launcher
echo   Folder: %~dp0
echo ===================================================
echo.

REM 1. Hentikan instance lama jika ada
echo [1/3] Menghentikan instance proses lama...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'main.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | Where-Object { $_.CommandLine -match 'server.js' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul
timeout /t 2 /nobreak >nul

REM 2. Jalankan GoPay Gateway
echo [2/3] Menjalankan GoPay Gateway (port 3005)...
start "GoPay Gateway Port 3005" /min cmd /c "cd /d \"%~dp0gopay-gateway\" && node server.js"
timeout /t 4 /nobreak >nul

REM 3. Jalankan Bot Telegram
echo [3/3] Menjalankan Bot Telegram (main.py)...
echo.
echo ===================================================
echo   Semua servis berjalan! Tekan Ctrl+C untuk keluar.
echo ===================================================
echo.

python main.py

pause
