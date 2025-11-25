# Guía de Actualización y Compilación - YouTube Downloader

Este documento detalla los pasos necesarios para generar una nueva versión del programa (`.exe` e Instalador) después de realizar cambios en el código fuente (`youtube_downloader.py`).

## 📋 Requisitos Previos
Asegúrate de que los siguientes archivos estén en la carpeta del proyecto antes de empezar:
- `ffmpeg.exe` y `ffprobe.exe` (Necesarios para la compilación).
- `build_exe.bat` (Script de automatización de PyInstaller).
- `setup_script.iss` (Script de Inno Setup).

---

## 🚀 Paso 1: Generar el nuevo Ejecutable (.exe)

Cada vez que modifiques el código Python, el `.exe` antiguo queda obsoleto.

1. Guarda los cambios en tu archivo `youtube_downloader.py`.
2. Haz doble clic en el archivo **`build_exe.bat`**.
3. Se abrirá una ventana negra realizando el proceso. Espera a que termine.
4. Al finalizar, verás el mensaje: `NUEVO EXE CREADO EN LA CARPETA DIST`.

> **Resultado:** El nuevo archivo `YTDownloader.exe` se habrá generado dentro de la carpeta `dist`.

---

## 📦 Paso 2: Crear el Instalador Actualizado

Una vez tengas el nuevo `.exe`, debes empaquetarlo para que los usuarios puedan instalar la nueva versión.

1. Abre el programa **Inno Setup Compiler**.
2. Abre tu archivo de script `.iss` (ej. `setup_script.iss`).
3. **IMPORTANTE:** Busca la línea de la versión al principio del archivo y aumenta el número:
   ```iss
   #define MyAppVersion "1.1"  <-- Cambia esto (ej. de 1.0 a 1.1)