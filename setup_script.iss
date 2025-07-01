; ===================================================================
; Inno Setup Script for TagCleric v1.1.0
; ===================================================================

[Setup]
; アプリケーションの基本情報
AppName=TagCleric
AppVersion=1.1.0
AppPublisher=EL bereth
AppPublisherURL=https://github.com/nicobtan/TagCleric
AppSupportURL=https://portfoliopage-25077.web.app/#/tagcleric
AppUpdatesURL=https://github.com/nicobtan/tagcleric
; インストーラーの基本設定
DefaultDirName={autopf}\TagCleric
DefaultGroupName=TagCleric
DisableProgramGroupPage=yes
LicenseFile=EULA.txt
OutputBaseFilename=TagCleric_v1.1.0_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ja"; MessagesFile: "compiler:Languages\Japanese.isl"

[Files]
; ここに、インストーラーに含めるファイルを指定します。
; Source: "配布元フォルダにあるファイル"; DestDir: "{app}（インストール先フォルダ）"; Flags: ignoreversion
Source: "dist\TagCleric.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TagClericIcon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\EULA.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\rename_prompts.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\lang\*"; DestDir: "{app}\lang"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; スタートメニューとデスクトップに作成するショートカットの設定
Name: "{group}\TagCleric"; Filename: "{app}\TagCleric.exe"
Name: "{group}\{cm:UninstallProgram,TagCleric}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TagCleric"; Filename: "{app}\TagCleric.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TagCleric.exe"; Description: "{cm:LaunchProgram,TagCleric}"; Flags: nowait postinstall skipifsilent

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone
