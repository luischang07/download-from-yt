# YouTube Downloader Pro

Aplicación de escritorio profesional para descargar videos y audio de YouTube, con reproductor integrado, cola de descargas y gestión de biblioteca.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## 🚀 Características Principales

- **📺 Descarga Versátil**: Videos en 4K, 1080p, 720p o solo Audio (MP3).
- **📋 Cola de Descargas**: Agrega múltiples videos y descárgalos uno tras otro automáticamente.
- **⏯️ Reproductor Integrado**: Previsualiza videos antes de bajar y reproduce tus descargas sin salir de la app (Motor VLC).
- **🔔 Notificaciones Inteligentes**: Avisos de escritorio nativos cuando tus descargas terminan.
- **🔄 Actualizador Automático**: Mantén el motor de descarga (`yt-dlp`) siempre al día con un solo clic.
- **📂 Biblioteca Multimedia**: Gestiona, busca y reproduce tus archivos descargados fácilmente.
- **🎨 Interfaz Moderna**: Diseño oscuro/claro con CustomTkinter, fluido y fácil de usar.

## 🛠️ Instalación y Uso

### Requisitos Previos
- Python 3.8 o superior
- Conexión a Internet

### Instalación Rápida

1. **Clonar o Descargar** este repositorio.
2. **Ejecutar el script de instalación** (Windows):
   ```powershell
   ./setup_ffmpeg.ps1  # Configura FFmpeg automáticamente
   ```
3. **Instalar dependencias de Python**:
   ```powershell
   pip install -r requirements.txt
   ```

### Ejecutar la Aplicación
```powershell
python main.py
```

## 📦 Estructura del Proyecto (MVC)

El proyecto sigue una arquitectura Modelo-Vista-Controlador para facilitar el mantenimiento:

- **`app/model.py`**: Lógica de negocio, gestión de descargas (`yt-dlp`), manejo de archivos y datos.
- **`app/view.py`**: Interfaz gráfica (GUI) construida con `customtkinter`.
- **`app/controller.py`**: Intermediario que gestiona la interacción entre el usuario y la lógica.
- **`app/player_frame.py`**: Componente reutilizable del reproductor de video (VLC).

## 🔧 Dependencias Clave

- `yt-dlp`: El motor de descarga más potente y actualizado.
- `customtkinter`: UI moderna y atractiva.
- `python-vlc`: Bindings para el reproductor VLC.
- `plyer`: Notificaciones nativas del sistema.
- `Pillow`: Manejo de imágenes y miniaturas.

## 📝 Notas Adicionales

- **FFmpeg**: La aplicación busca FFmpeg automáticamente en la carpeta del proyecto o en el sistema. Es necesario para unir video+audio en alta calidad y convertir a MP3.
- **VLC**: Se requiere tener las librerías de VLC (`libvlc.dll`) accesibles o VLC instalado en el sistema para que funcione el reproductor integrado.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Siéntete libre de usarlo, modificarlo y distribuirlo.
