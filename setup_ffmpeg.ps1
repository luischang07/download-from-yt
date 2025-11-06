# Script de inicio para asegurar que ffmpeg esté disponible
# Agregar esto al final de tu perfil de PowerShell

$ffmpegPath = "C:\ProgramData\chocolatey\bin"

if (Test-Path $ffmpegPath) {
  if ($env:Path -notlike "*$ffmpegPath*") {
    $env:Path += ";$ffmpegPath"
    Write-Host "[OK] ffmpeg agregado al PATH de esta sesion" -ForegroundColor Green
  }
}
