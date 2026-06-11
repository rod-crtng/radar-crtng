@echo off
chcp 65001 >nul
cd /d "D:\BUSINESS\Creating\RADAR_CRTNG\radar_kit"
echo.
echo  ===========================================
echo   RADAR CRTNG - publicando atualizacao...
echo  ===========================================
echo.
"C:\Users\rod\AppData\Local\Programs\Python\Python313\python.exe" gerar_radar.py
echo.
echo  ===========================================
echo   Pronto. O painel atualiza em ~30s:
echo   https://radar-crtng.vercel.app
echo  ===========================================
echo.
pause
