@echo off
title P2P Crypto Bot
cd /d "%~dp0"

echo ============================================
echo   P2P Crypto Bot - Launcher
echo   Folder: %~dp0
echo ============================================
echo.

REM Hentikan instance lama agar tidak bentrok (duplikat polling token).
REM Filter Name='python.exe' agar script TIDAK membunuh dirinya sendiri.
echo [1/3] Menghentikan instance main.py lama...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'main.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul
timeout /t 3 /nobreak >nul

echo [2/3] Memeriksa gateway GoPay (port 3000)...
powershell -NoProfile -Command "try { $h = Invoke-RestMethod -Uri 'http://127.0.0.1:3000/health' -TimeoutSec 4; Write-Output ('   Gateway: ' + $h.status) } catch { Write-Output '   GATEWAY DOWN - jalankan: cd gopay-gateway ^&^& node server.js' }"

echo [3/3] Menjalankan bot (log: bot.log / bot_err.log)...
echo.
echo   Tekan Ctrl+C untuk menghentikan bot.
echo ============================================
echo.

python main.py >> bot.log 2>> bot_err.log

echo.
echo Bot berhenti. Jendela akan ditutup dalam 5 detik...
timeout /t 5 /nobreak >nul
