# Guía para Crear el Instalador (.exe) - YouTube Downloader

Esta guía explica cómo convertir el script de Python en un programa instalable profesional para Windows. El proceso consta de dos partes: compilar el código y crear el instalador.

---

## 📋 Requisitos Previos

1. **Archivos FFmpeg:**
   Asegúrate de tener los archivos `ffmpeg.exe` y `ffprobe.exe` en la carpeta raíz del proyecto (`c:\Users\Hirai Momo\Downloads\download-from-yt`).
   *Si no los tienes, descárgalos de [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip) (versión essentials).*

2. **Software Necesario:**
   - Tener instalado **Inno Setup** (descargar de [jrsoftware.org](https://jrsoftware.org/isdl.php)).
   - Tener la librería **PyInstaller** instalada en Python:
     ```bash
     pip install pyinstaller
     ```

---

## 🚀 Paso 1: Crear el Ejecutable (.exe)

Este paso empaqueta tu código Python, las librerías y FFmpeg en un solo archivo.

1. Abre la terminal en la carpeta del proyecto.
2. Ejecuta el siguiente comando (copia y pega):

```powershell
py -3 -m PyInstaller --noconfirm --onefile --windowed --name "YTDownloader" --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import "vlc" --collect-all "customtkinter" youtube_downloader.py