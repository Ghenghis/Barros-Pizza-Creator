#define AppVersion "1.6.0"
#ifndef StageDir
  #error StageDir must point at the prepared offline payload.
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
AppId={{A53921F4-BE6E-4D31-B4B1-6243950EAE16}
AppName=Barro's Pizza Creator
AppVersion={#AppVersion}
AppVerName=Barro's Pizza Creator {#AppVersion}
AppPublisher=Ghenghis
AppPublisherURL=https://github.com/Ghenghis/Barros-Pizza-Creator
AppSupportURL=https://github.com/Ghenghis/Barros-Pizza-Creator/issues
DefaultDirName={autopf}\Barros Pizza Creator
DefaultGroupName=Barro's Pizza Creator
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#OutputDir}
OutputBaseFilename=Barros_Pizza_Creator_v1.6.0_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern dynamic
UninstallDisplayIcon={app}\Barros_Pizza_Creator_Manager.exe
VersionInfoVersion=1.6.0.0
VersionInfoCompany=Ghenghis
VersionInfoDescription=Barro's Pizza Creator 1.6 Windows installer
VersionInfoProductName=Barro's Pizza Creator
VersionInfoProductVersion=1.6.0.0
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Barro's Pizza Creator Manager"; Filename: "{app}\Barros_Pizza_Creator_Manager.exe"
Name: "{group}\Launch Pizza Creator"; Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Parameters: "--launch"
Name: "{group}\Configure AI and Voices"; Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Parameters: "--configure"
Name: "{group}\Run Diagnostics"; Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Parameters: "--diagnose"
Name: "{group}\Uninstall Barro's Pizza Creator"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Barro's Pizza Creator"; Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "SOFTWARE\BarrosPizzaCreator"; ValueType: string; ValueName: "GameRoot"; ValueData: "{code:GetGameRoot}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\BarrosPizzaCreator"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Description: "Open Barro's Pizza Creator Manager"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\Barros_Pizza_Creator_Manager.exe"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveBarrosAddon"

[Code]
var
  GameRootPage: TInputDirWizardPage;

function IsGameRoot(const Root: String): Boolean;
begin
  Result := FileExists(AddBackslash(Root) + 'Pizza Connection 3 - Pizza Creator.exe') and
    FileExists(AddBackslash(Root) + 'Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp.dll') and
    FileExists(AddBackslash(Root) + 'Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp-firstpass.dll');
end;

function DetectGameRoot(): String;
var
  SteamPath: String;
  Candidate: String;
begin
  Result := ExpandConstant('{param:GameRoot|}');
  if IsGameRoot(Result) then Exit;

  if RegQueryStringValue(HKLM, 'SOFTWARE\BarrosPizzaCreator', 'GameRoot', Candidate) and IsGameRoot(Candidate) then
  begin
    Result := Candidate;
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', SteamPath) then
  begin
    Candidate := AddBackslash(SteamPath) + 'steamapps\common\Pizza Connection 3 - Pizza Creator';
    if IsGameRoot(Candidate) then
    begin
      Result := Candidate;
      Exit;
    end;
  end;
  Candidate := ExpandConstant('{pf32}\Steam\steamapps\common\Pizza Connection 3 - Pizza Creator');
  if IsGameRoot(Candidate) then
  begin
    Result := Candidate;
    Exit;
  end;
  Candidate := 'S:\Unity_Games\PC3 - Pizza Creator';
  if IsGameRoot(Candidate) then Result := Candidate else Result := '';
end;

procedure InitializeWizard();
begin
  GameRootPage := CreateInputDirPage(wpSelectDir,
    'Select Pizza Creator',
    'Choose the existing Pizza Connection 3 - Pizza Creator folder.',
    'The installer verifies the exact 0.11.272 game build before adding Barro''s files. The commercial game is not included.',
    False, '');
  GameRootPage.Add('');
  GameRootPage.Values[0] := DetectGameRoot();
end;

function GetGameRoot(Param: String): String;
begin
  Result := RemoveBackslashUnlessRoot(GameRootPage.Values[0]);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = GameRootPage.ID) and not IsGameRoot(GameRootPage.Values[0]) then
  begin
    MsgBox('Select the folder containing the complete Pizza Connection 3 - Pizza Creator 0.11.272 installation.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Parameters: String;
begin
  if CurStep = ssPostInstall then
  begin
    Parameters := '--install --game-root "' + GetGameRoot('') + '"';
    if not Exec(ExpandConstant('{app}\Barros_Pizza_Creator_Manager.exe'), Parameters,
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      RaiseException('Could not start the Barro''s installation manager.');
    if ResultCode <> 0 then
      RaiseException('The selected Pizza Creator installation did not pass verification or could not be updated. Error code: ' + IntToStr(ResultCode));
  end;
end;
