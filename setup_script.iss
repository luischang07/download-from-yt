; Script generado para Inno Setup
; Reemplaza las rutas con las de tu PC

#define MyAppName "YouTube Downloader"
#define MyAppVersion "1.1"
#define MyAppPublisher "Hirai Momo"
#define MyAppExeName "YTDownloader.exe"

[Setup]
; Identificador único (Genera uno nuevo en Inno Setup: Tools -> Generate GUID)
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Crea el instalador en la carpeta "Output" dentro de tu proyecto
OutputDir=Output
OutputBaseFilename=Instalador_YTDownloader
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; El archivo principal generado por PyInstaller
Source: "C:\Users\Hirai Momo\Downloads\Yt-Downloader\dist\YTDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

; NOTA SOBRE VLC:
; No podemos empaquetar VLC entero legalmente dentro del exe fácilmente, 
; pero podemos verificar si existe o abrir la web de descarga.
; Opcionalmente, si tienes el instalador de VLC (vlc-3.0.20-win64.exe) descargado, puedes incluirlo:
; Source: "vlc-installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Si decides incluir el instalador de VLC, descomenta esto:
; Filename: "{tmp}\vlc-installer.exe"; Parameters: "/S"; StatusMsg: "Instalando VLC Media Player (Requerido)..."; Check: VlcNotInstalled

[Code]
// Función opcional para verificar si VLC existe (Básico)
function VlcNotInstalled: Boolean;
begin
  Result := not FileExists(ExpandConstant('{commonpf}\VideoLAN\VLC\vlc.exe'));
end;