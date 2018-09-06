#define ApplicationVersion GetFileVersion('dist/main.exe')

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{9AE83186-BD26-4000-ACD6-9EF66D7D4CF0}
AppName=Jonathan's Backupper
AppVersion={#ApplicationVersion}
VersionInfoVersion={#ApplicationVersion}
AppPublisher=OrOrg Development, Inc.
AppPublisherURL=https://github.com/JonathanMaes/Backupper
AppSupportURL=https://github.com/JonathanMaes/Backupper/issues
AppUpdatesURL=https://github.com/JonathanMaes/Backupper/releases
DefaultDirName={pf}\Jonathan's Backupper
DefaultGroupName=Jonathan's Backupper
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename="JonathansBackupper_installer_{#ApplicationVersion}"
SetupIconFile=dist\icon.ico
Compression=lzma
SolidCompression=yes       
DisableDirPage=auto
DisableProgramGroupPage=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Jonathan's Backupper"; Filename: "{app}\main.exe"
Name: "{commondesktop}\Jonathan's Backupper"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,Jonathan's Backupper}"; Flags: nowait postinstall skipifsilent