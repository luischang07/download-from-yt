@echo off
echo Borrando versiones anteriores...
rmdir /s /q build dist

echo Creando nuevo ejecutable...
py -3 -m PyInstaller --noconfirm --onefile --windowed --name "YTDownloader" --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import "vlc" --collect-all "customtkinter" youtube_downloader.py

echo.
echo ==========================================
echo    NUEVO EXE CREADO EN LA CARPETA DIST
echo ==========================================
pause