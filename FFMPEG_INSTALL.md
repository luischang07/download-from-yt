# Instalación de FFmpeg (Opcional)

FFmpeg es necesario solo si quieres descargar videos en la máxima calidad posible combinando streams de video y audio separados.

**La aplicación funciona SIN ffmpeg**, pero con formatos pre-combinados que YouTube ofrece.

## ¿Necesito FFmpeg?

- ✅ **NO** si estás conforme con las calidades disponibles (720p, 1080p en formato único)
- ⚠️ **SÍ** si quieres la máxima calidad posible (4K, 8K) que requiere combinar video y audio

## Instalación en Windows

### Opción 1: Con Chocolatey (Recomendado)

1. Instala Chocolatey si no lo tienes: https://chocolatey.org/install

2. Ejecuta en PowerShell como Administrador:

```powershell
choco install ffmpeg
```

### Opción 2: Manual

1. Descarga FFmpeg desde: https://www.gyan.dev/ffmpeg/builds/

   - Descarga la versión "ffmpeg-release-essentials.zip"

2. Extrae el ZIP a una carpeta, por ejemplo: `C:\ffmpeg`

3. Agrega FFmpeg al PATH:

   - Abre "Variables de entorno" en Windows
   - En "Variables del sistema", busca "Path"
   - Haz clic en "Editar"
   - Agrega: `C:\ffmpeg\bin`
   - Haz clic en "Aceptar"

4. Reinicia PowerShell y verifica:

```powershell
ffmpeg -version
```

### Opción 3: Con Scoop

```powershell
scoop install ffmpeg
```

## Verificar Instalación

Ejecuta en PowerShell:

```powershell
ffmpeg -version
```

Si ves la versión de ffmpeg, está instalado correctamente.

## Después de Instalar FFmpeg

Una vez instalado FFmpeg, la aplicación podrá:

- Descargar videos en 4K y 8K
- Combinar el mejor video con el mejor audio
- Ofrecer más opciones de calidad

. .\setup_ffmpeg.ps1
