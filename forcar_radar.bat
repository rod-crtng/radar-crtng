@echo off
REM Forca a republicacao do radar mesmo sem mudanca (ex.: apos trocar o template).
REM O atualizar_radar.bat normal NAO precisa de --force: o script publica sozinho quando ha mudanca.
cd /d "D:\BUSINESS\Creating\RADAR_CRTNG\radar_kit"
python gerar_radar.py --force
pause
