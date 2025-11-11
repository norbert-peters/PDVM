; PDVM-System v0.9 - Inno Setup Script
; Erstellt einen Windows-Installer
;
; VORAUSSETZUNGEN:
; - Inno Setup 6.x installiert (https://jrsoftware.org/isdl.php)
; - EXE bereits mit PyInstaller erstellt (build_exe.ps1)
;
; VERWENDUNG:
; - Öffne setup.iss in Inno Setup
; - Klicke auf "Compile" (oder F9)
; - Installer wird in installer/ erstellt

[Setup]
; App-Informationen
AppName=PDVM-System
AppVersion=0.9
AppPublisher=Norbert Peters
AppPublisherURL=https://github.com/norbert-peters/PDVM
AppSupportURL=https://github.com/norbert-peters/PDVM/issues
AppUpdatesURL=https://github.com/norbert-peters/PDVM/releases

; Installation
DefaultDirName={autopf}\PDVM-System
DefaultGroupName=PDVM-System
AllowNoIcons=yes

; Output
OutputDir=installer
OutputBaseFilename=PDVM-System-v0.9-Setup
SetupIconFile=

; Kompression
Compression=lzma2/ultra64
SolidCompression=yes

; Visuell
WizardStyle=modern
DisableWelcomePage=no

; Berechtigungen
PrivilegesRequired=admin

; Architektur
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Versionierung
VersionInfoVersion=0.9.0.0
VersionInfoCompany=Norbert Peters
VersionInfoDescription=PDVM-System - Personal Daten Verwaltungs Management
VersionInfoCopyright=Copyright (C) 2025 Norbert Peters

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Haupt-EXE
Source: "dist\PDVM-System-v0.9.exe"; DestDir: "{app}"; Flags: ignoreversion

; Daten-Verzeichnis
Source: "Daten\*"; DestDir: "{app}\Daten"; Flags: ignoreversion recursesubdirs createallsubdirs

; Dokumentation
Source: "VERSION_0_9_RELEASE.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALLATION_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion

; Bugfix-Dokumentation (optional)
Source: "BUGFIX_ROUND_*.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
; Startmenü
Name: "{group}\PDVM-System"; Filename: "{app}\PDVM-System-v0.9.exe"
Name: "{group}\Dokumentation"; Filename: "{app}\VERSION_0_9_RELEASE.md"
Name: "{group}\{cm:UninstallProgram,PDVM-System}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{autodesktop}\PDVM-System"; Filename: "{app}\PDVM-System-v0.9.exe"; Tasks: desktopicon

; Quick Launch (optional)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\PDVM-System"; Filename: "{app}\PDVM-System-v0.9.exe"; Tasks: quicklaunchicon

[Run]
; Datenbank initialisieren (nur bei erster Installation)
Filename: "{app}\PDVM-System-v0.9.exe"; Parameters: "--init-db"; StatusMsg: "Initialisiere Datenbank..."; Flags: runhidden waituntilterminated; Check: not DirExists(ExpandConstant('{app}\Daten\auth.db'))

; Anwendung nach Installation starten (optional)
Filename: "{app}\PDVM-System-v0.9.exe"; Description: "{cm:LaunchProgram,PDVM-System}"; Flags: nowait postinstall skipifsilent

[Code]
{ Custom Code für spezielle Installationslogik }

function InitializeSetup(): Boolean;
begin
  Result := True;
  
  { Prüfe ob alte Version installiert ist }
  if RegKeyExists(HKLM, 'Software\PDVM-System') then
  begin
    if MsgBox('Eine ältere Version von PDVM-System wurde gefunden.' + #13#13 +
              'Möchten Sie diese deinstallieren?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      { Deinstallation wird automatisch durchgeführt }
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Registrierung für Versionierung }
    RegWriteStringValue(HKLM, 'Software\PDVM-System', 'Version', '0.9');
    RegWriteStringValue(HKLM, 'Software\PDVM-System', 'InstallPath', ExpandConstant('{app}'));
  end;
end;

[UninstallDelete]
{ Entferne Log-Dateien bei Deinstallation }
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\.pdvm_main_starts"

[Registry]
{ Registrierungs-Einträge für Windows }
Root: HKLM; Subkey: "Software\PDVM-System"; ValueType: string; ValueName: "Version"; ValueData: "0.9"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\PDVM-System"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Messages]
german.WelcomeLabel2=Willkommen beim PDVM-System v0.9 Setup!%n%nDies wird PDVM-System auf Ihrem Computer installieren.%n%nPDVM-System ist eine professionelle Datenverwaltungs-Software für Stammdaten, Finanzdaten und mehr.
