# Registro de Cambios (Changelog)

Todas las modificaciones notables en este proyecto serán documentadas en este archivo.

## [1.2.0] - 2025-11-30
### Añadido
- **Cola de Descargas**: Ahora puedes agregar múltiples videos a una lista y descargarlos secuencialmente.
- **Reproductor Integrado**: Nuevo reproductor multimedia basado en VLC para previsualizar videos y reproducir archivos descargados sin salir de la app.
- **Notificaciones de Escritorio**: Alertas nativas de Windows cuando finaliza una descarga o la cola completa.
- **Actualizador Automático**: Botón para actualizar el motor `yt-dlp` directamente desde la interfaz.
- **Biblioteca Mejorada**: Visualización de archivos descargados con miniaturas y botón de reproducción rápida.
- **Arquitectura MVC**: Reestructuración completa del código en Modelo-Vista-Controlador para mayor estabilidad.

### Cambiado
- **Interfaz de Usuario**: Barra lateral de navegación mejorada, notificaciones "toast" no intrusivas.
- **Gestión de Archivos**: Detección automática de nombres duplicados para evitar sobrescrituras accidentales.
- **Motor de Descarga**: Optimización de parámetros de `yt-dlp` para mejor compatibilidad.

## [1.1.0] - 2025-11-28
### Añadido
- Soporte para FFmpeg local (portable).
- Scripts de instalación y construcción (`build_exe.bat`).

## [1.0.0] - 2025-11-25
### Lanzamiento Inicial
- Descarga de videos y audio de YouTube.
- Selección de calidad.
- Interfaz básica con CustomTkinter.
