@echo off
title Dragon Mailer - Create Shortcut
color 0A

echo.
echo  ============================================
echo     DRAGON MAILER - SHORTCUT CREATOR
echo  ============================================
echo.
echo  Creating desktop and Start Menu shortcuts...
echo.

cd /d "%~dp0"

:: Run the PowerShell script to create shortcuts
powershell -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"

echo.
echo  Done! You can now start Dragon Mailer from:
echo    - Desktop shortcut
echo    - Start Menu
echo.
pause
