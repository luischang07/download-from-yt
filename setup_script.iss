; Script de instalación para YT Downloader
; Requiere Inno Setup para compilar

#define MyAppName "YT Downloader"
#define MyAppVersion "2.0"
#define MyAppPublisher "Luis Chang & Fasutto Momo"
#define MyAppExeName "YTDownloader.exe"

[Setup]
; Identificador único de la aplicación
AppId={{8A4B2C1D-E5F6-4321-8765-1234567890AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Instalar en Archivos de Programa por defecto
DefaultDirName={autopf}\{#MyAppName}
; Nombre del grupo en el menú inicio
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Carpeta donde se guardará el instalador generado
OutputDir=Output
OutputBaseFilename=Instalador_YTDownloader_v{#MyAppVersion}
; Compresión máxima para reducir tamaño (importante ya que incluye VLC)
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Requiere permisos de administrador para instalar en Program Files
PrivilegesRequired=admin
; Icono del instalador (opcional, usa el predeterminado si no tienes uno)
; SetupIconFile=icon.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia el ejecutable principal
Source: "dist\YTDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion
; Copia la carpeta VLC completa junto al ejecutable
Source: "vlc\*"; DestDir: "{app}\vlc"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copia FFmpeg y FFprobe junto al ejecutable
Source: "ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Código Pascal Script opcional para validaciones avanzadas (no necesario por ahora)
// Función opcional para verificar si VLC existe (Básico)
function VlcNotInstalled: Boolean;
begin
  Result := not FileExists(ExpandConstant('{commonpf}\VideoLAN\VLC\vlc.exe'));
end;