$vlcUrl = "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.zip"
$zipPath = "vlc.zip"
$extractPath = "vlc_temp"
$finalPath = "vlc"

Write-Host "Descargando VLC Portable (aprox 40MB)... Esto puede tardar unos minutos." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $vlcUrl -OutFile $zipPath
} catch {
    Write-Error "Error al descargar VLC. Verifica tu conexión a internet."
    exit
}

Write-Host "Extrayendo archivos..." -ForegroundColor Cyan
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

Write-Host "Configurando carpeta vlc..." -ForegroundColor Cyan
# El zip contiene una carpeta vlc-3.0.20 dentro. Movemos su contenido a ./vlc
$innerFolder = Get-ChildItem -Path $extractPath -Directory | Select-Object -First 1
if (Test-Path $finalPath) { Remove-Item -Path $finalPath -Recurse -Force }
Move-Item -Path $innerFolder.FullName -Destination $finalPath

Write-Host "Limpiando archivos temporales..." -ForegroundColor Cyan
Remove-Item $zipPath
Remove-Item $extractPath -Recurse -Force

Write-Host "¡VLC Portable instalado correctamente en $finalPath!" -ForegroundColor Green
Write-Host "Ahora la aplicación usará esta versión local de VLC." -ForegroundColor Green
