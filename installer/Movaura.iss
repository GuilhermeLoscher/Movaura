#define MyAppName "Movaura"
#define MyAppVersion "0.9.0"
#define MyAppPublisher "Guilherme Loscher (GL)"
#define MyAppExeName "Movaura.exe"

[Setup]
AppId={{4A62B69C-AF84-4F5C-A706-8E45054B921D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Movaura
DefaultGroupName=Movaura
DisableProgramGroupPage=yes
OutputDir=..\release\installer
OutputBaseFilename=Movaura-Setup-0.9.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
CloseApplications=force
RestartApplications=no
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\movaura.ico
AppCopyright=Copyright (C) 2026 Guilherme Loscher (GL)
VersionInfoCompany=Guilherme Loscher (GL)
VersionInfoDescription=Movaura - live wallpapers para Windows
VersionInfoProductName=Movaura
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright=Copyright (C) 2026 Guilherme Loscher (GL)

[Languages]
Name: "brazilianportuguese"; MessagesFile: "BrazilianPortuguese.isl"

[Files]
Source: "..\release\standalone-commercial\Movaura\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\release\standalone-commercial\Movaura\Movaura.exe"; DestDir: "{app}"; DestName: "Movaura.scr"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LEIA-ME-PRIMEIRO.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\AUTHORS.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Movaura"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--control-panel"
Name: "{autodesktop}\Movaura"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--control-panel"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"
Name: "startup"; Description: "Iniciar o Movaura com o Windows"; GroupDescription: "Inicializacao:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--enable-startup"; Flags: runhidden waituntilterminated; Tasks: startup
Filename: "{app}\{#MyAppExeName}"; Parameters: "--control-panel"; Description: "Abrir o Movaura"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--disable-startup"; Flags: runhidden waituntilterminated skipifdoesntexist; RunOnceId: "DisableStartup"
Filename: "{cmd}"; Parameters: "/C taskkill /IM Movaura.exe /F >NUL 2>&1 & taskkill /IM movaura_native_compositor.exe /F >NUL 2>&1"; Flags: runhidden waituntilterminated; RunOnceId: "StopMovaura"
Filename: "{app}\{#MyAppExeName}"; Parameters: "--restore-system-wallpaper"; Flags: runhidden waituntilterminated skipifdoesntexist; RunOnceId: "RestoreWallpaper"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Exec(
    ExpandConstant('{cmd}'),
    '/C taskkill /IM Movaura.exe /F >NUL 2>&1 & taskkill /IM movaura_native_compositor.exe /F >NUL 2>&1',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  Result := '';
end;
