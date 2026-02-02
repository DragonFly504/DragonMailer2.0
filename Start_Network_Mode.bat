@echo off
title Dragon Mailer - Network Mode
cd /d "%~dp0"
echo.
echo  ========================================
echo     🐉 Dragon Mailer v1.1.0
echo     NETWORK MODE - Access from any PC
echo  ========================================
echo.

:: Get the local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo  Your PC's IP Address: %IP%
echo.
echo  ----------------------------------------
echo  ACCESS FROM OTHER PCs:
echo    http://%IP%:8501
echo  ----------------------------------------
echo.
echo  Make sure:
echo    1. Password protection is ENABLED in Settings
echo    2. Windows Firewall allows port 8501
echo    3. Both PCs are on the same network
echo.
echo  Press Ctrl+C to stop the server.
echo.

python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
pause
