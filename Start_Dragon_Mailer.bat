@echo off
title Dragon Mailer - Starting...
cd /d "%~dp0"
echo.
echo  ========================================
echo     🐉 Dragon Mailer v1.1.0
echo     Starting your messaging app...
echo  ========================================
echo.
echo  LOCAL ACCESS:  http://localhost:8501
echo.
echo  For NETWORK access (other PCs), use:
echo    Start_Network_Mode.bat
echo.
echo  Press Ctrl+C to stop the server.
echo.
python -m streamlit run app.py --server.port 8501
pause
