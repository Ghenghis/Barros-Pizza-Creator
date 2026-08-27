#define MyAppName "Barro's Pizza Creator AI Designer"
#define MyAppVersion "1.3.0-rc1"
#define MyAppPublisher "Ghenghis / Barro's Pizza"

[Setup]
AppId={{7D8B8BEA-826C-4F7A-92C7-A1C12D36E1B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\BarrosPizzaCreatorTools
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\releases
OutputBaseFilename=Barros_Pizza_Creator_AI_Designer_v1.3.0-rc1_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName} tools

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git\*,releases\*,evidence\*,__pycache__\*,*.pyc,backend\settings.json,backend\data\conversation_history.json"

[Icons]
Name: "{autoprograms}\Barro's Pizza Creator\Install AI Designer"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\INSTALL_Barros_AI_Designer.ps1"""; WorkingDir: "{app}"
Name: "{autoprograms}\Barro's Pizza Creator\Diagnose AI Designer"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\DIAGNOSE_Barros_AI.ps1"""; WorkingDir: "{app}"
Name: "{autoprograms}\Barro's Pizza Creator\Uninstall from game"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\UNINSTALL_Barros_AI_Designer.ps1"""; WorkingDir: "{app}"

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\INSTALL_Barros_AI_Designer.ps1"""; Description: "Install into S:\Unity_Games\PC3 - Pizza Creator now"; Flags: postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
