@echo off
title Dragon Mailer - First Time Setup
cd /d "%~dp0"

echo.
echo  ========================================
echo     🐉 Dragon Mailer v2.0 - Setup
echo  ========================================
echo.
echo  This will:
echo    1. Install required Python packages
echo    2. Create desktop shortcut
echo    3. Create config folder
echo.
echo  Press any key to continue...
pause >nul

echo.
echo  [1/3] Installing Python packages...
pip install streamlit>=1.0.0 --quiet
if errorlevel 1 (
    echo  ⚠️  Some packages may have failed. Trying with --user flag...
    pip install streamlit>=1.0.0 --user --quiet
)

echo  [2/3] Creating config folder...
if not exist "config" mkdir config

echo  [3/3] Creating Desktop shortcut...

:: Get the desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

:: Create a VBS script to make a proper shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\Dragon Mailer.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%~dp0Start_Dragon_Mailer.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Dragon Mailer - Bulk Email and SMS" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "shell32.dll,14" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo  ========================================
echo     ✅ Setup Complete!
echo  ========================================
echo.
echo  A shortcut "Dragon Mailer" has been
echo  created on your Desktop.
echo.
echo  Double-click it to start the app!
echo.
echo  Go to Settings to enable login protection.
echo.
pause
