@echo off
echo Opening Port 8000 for FastAPI...
netsh advfirewall firewall add rule name="FastAPI_Port_8000" dir=in action=allow protocol=TCP localport=8000
echo Done. Press any key to close.
pause > nul
