# Script para agregar ffmpeg al PATH del usuario
Write-Host "Buscando ffmpeg en ubicaciones comunes..." -ForegroundColor Cyan

$commonPaths = @(
  "C:\ffmpeg\bin",
  "C:\Program Files\ffmpeg\bin",
  "C:\Program Files (x86)\ffmpeg\bin",
  "$env:ProgramData\chocolatey\bin",
  "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
)

$ffmpegPath = $null

# Buscar en ubicaciones comunes
foreach ($path in $commonPaths) {
  if (Test-Path "$path\ffmpeg.exe") {
    $ffmpegPath = $path
    Write-Host "[OK] ffmpeg encontrado en: $path" -ForegroundColor Green
    break
  }
}

# Si no se encuentra, buscar en todo el disco C:
if (-not $ffmpegPath) {
  Write-Host "Buscando ffmpeg en el disco C: (esto puede tomar un momento)..." -ForegroundColor Yellow
  $result = Get-ChildItem -Path "C:\" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($result) {
    $ffmpegPath = $result.DirectoryName
    Write-Host "[OK] ffmpeg encontrado en: $ffmpegPath" -ForegroundColor Green
  }
}

if (-not $ffmpegPath) {
  Write-Host "[ERROR] No se pudo encontrar ffmpeg.exe" -ForegroundColor Red
  Write-Host "Por favor, instala ffmpeg siguiendo las instrucciones en FFMPEG_INSTALL.md" -ForegroundColor Yellow
  exit 1
}

# Obtener el PATH actual del usuario
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Verificar si ya esta en el PATH
if ($userPath -split ';' | Where-Object { $_ -eq $ffmpegPath }) {
  Write-Host "[OK] ffmpeg ya esta en el PATH del usuario" -ForegroundColor Green
}
else {
  # Agregar al PATH del usuario
  $newPath = $userPath + ";" + $ffmpegPath
  [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
  Write-Host "[OK] ffmpeg agregado al PATH del usuario" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IMPORTANTE: Cierra y vuelve a abrir VSCode" -ForegroundColor Yellow
Write-Host "para que los cambios surtan efecto." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar en la sesion actual
$env:Path = $env:Path + ";" + $ffmpegPath
Write-Host "Verificando en la sesion actual:" -ForegroundColor Cyan
ffmpeg -version | Select-Object -First 3

Write-Host ""
Write-Host "[OK] Script completado exitosamente" -ForegroundColor Green
