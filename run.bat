@echo off
echo Activando entorno virtual...
call .venv\Scripts\activate.bat
echo.
echo Configurando ffmpeg...
set PATH=%PATH%;C:\ProgramData\chocolatey\bin
echo.
echo Ejecutando YouTube Downloader...
py -3  main.py
pause
