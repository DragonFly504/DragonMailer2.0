@echo off
title Allow Dragon Mailer Through Firewall
echo.
echo  ========================================
echo     🔥 Firewall Configuration
echo     Allow Dragon Mailer network access
echo  ========================================
echo.
echo  This will add a firewall rule to allow
echo  other PCs to connect to Dragon Mailer.
echo.
echo  Press any key to continue or Ctrl+C to cancel...
pause >nul

:: Add firewall rule (requires admin)
netsh advfirewall firewall add rule name="Dragon Mailer (Streamlit)" dir=in action=allow protocol=tcp localport=8501

echo.
echo  ✅ Firewall rule added!
echo  Other PCs can now connect to this PC on port 8501.
echo.
pause
