# YouTube Video Downloader

Aplicación con interfaz gráfica para descargar videos de YouTube con selección de calidad.

## Características

- 🎨 Interfaz gráfica moderna con CustomTkinter
- 📹 Descarga videos de YouTube en diferentes calidades
- 🎯 Selección de calidad/resolución del video
- 📁 Selección de carpeta de destino
- 📊 Barra de progreso de descarga
- 🔒 Descarga en segundo plano (no bloquea la interfaz)

## Instalación

### 1. Crear el entorno virtual

```powershell
python -m venv venv
```

### 2. Activar el entorno virtual

```powershell
.\venv\Scripts\Activate.ps1
```

Si tienes problemas con la política de ejecución, ejecuta:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

## Uso

### Ejecutar la aplicación

```powershell
python youtube_downloader.py
```

### Pasos para descargar un video:

1. **Pegar la URL**: Copia y pega el enlace del video de YouTube
2. **Obtener calidades**: Haz clic en "Obtener Calidades Disponibles"
3. **Seleccionar calidad**: Elige la calidad deseada del menú desplegable
4. **Elegir ubicación**: (Opcional) Cambia la carpeta de destino con el botón "Explorar"
5. **Descargar**: Haz clic en "Descargar Video"

## Dependencias

- **yt-dlp**: Librería para descargar videos de YouTube
- **customtkinter**: Framework moderno para interfaces gráficas
- **Pillow**: Procesamiento de imágenes

## Requisitos

- Python 3.8 o superior
- Windows, macOS o Linux

## Notas

- Los videos se descargan por defecto en la carpeta "Downloads" del usuario
- El formato final es MP4
- La aplicación muestra el progreso de descarga en tiempo real
- Se requiere conexión a Internet

## Solución de problemas

### Error de ejecución de scripts en PowerShell

Si al activar el entorno virtual aparece un error de política de ejecución:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error al descargar videos

- Verifica que la URL sea válida
- Asegúrate de tener conexión a Internet
- Algunos videos pueden estar restringidos por región o privacidad

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
