@echo off
title Dragon Mailer - First Time Setup
cd /d "%~dp0"

echo.
echo  ========================================
echo     DRAGON MAILER v2.0 - Setup
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
python -m pip install streamlit --quiet
if errorlevel 1 (
    echo  [!] Some packages may have failed. Trying with --user flag...
    python -m pip install streamlit --user --quiet
)

echo  [2/3] Creating config folder...
if not exist "config" mkdir config

echo  [3/3] Creating Desktop shortcut...

:: Get the desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

:: Create a simple batch file shortcut on desktop instead
echo @echo off > "%DESKTOP%\Dragon Mailer.bat"
echo cd /d "%~dp0" >> "%DESKTOP%\Dragon Mailer.bat"
echo start "" "%~dp0Start_Dragon_Mailer.bat" >> "%DESKTOP%\Dragon Mailer.bat"

echo.
echo  ========================================
echo     [OK] Setup Complete!
echo  ========================================
echo.
echo  A shortcut "Dragon Mailer.bat" has been
echo  created on your Desktop.
echo.
echo  Double-click it to start the app!
echo.
echo  Login: admin
echo.
pause
