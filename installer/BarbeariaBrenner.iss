; Barbearia Brenner Desktop — instalador completo para Windows x64.
; Gere com: .\installer\CRIAR_INSTALADOR.ps1 na raiz do projeto.
; Inno Setup 6.3+ (testar preferencialmente com Inno Setup 6 mais recente).

#define NomeAplicativo "Barbearia Brenner Desktop"
#define NomeExecutavel "BrennerDesktop.exe"
#define VersaoAplicativo "1.0.0"

[Setup]
; Preserve o AppId nas futuras versões para atualizar a mesma instalação.
AppId={{7D4390D1-BDB7-41F5-9536-2C44D4ED180F}
AppName={#NomeAplicativo}
AppVersion={#VersaoAplicativo}
AppVerName={#NomeAplicativo} {#VersaoAplicativo}
AppPublisher=Front Dev Studio
DefaultDirName={autopf}\Barbearia Brenner Desktop
DefaultGroupName=Barbearia Brenner
DisableProgramGroupPage=yes
WizardStyle=modern
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
PrivilegesRequired=admin
OutputDir=..\dist_instalador
OutputBaseFilename=Barbearia_Brenner_Setup_{#VersaoAplicativo}_x64
SetupIconFile=..\desktop\assets\brenner.ico
UninstallDisplayIcon={app}\{#NomeExecutavel}
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes
; A instalação NÃO toca nos dados de usuário em %LOCALAPPDATA%.
; O WebView2 é um runtime compartilhado do Windows e NÃO será desinstalado.

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
; Pré-requisito offline, dentro do próprio instalador. Extraído apenas se necessário.
; Mantenha esta linha antes de outras entradas quando usar SolidCompression.
Source: "redist\MicrosoftEdgeWebView2RuntimeInstallerX64.exe"; Flags: dontcopy noencryption

; PyInstaller --onedir já inclui Python, dependências e frontend React compilado.
Source: "..\dist\BrennerDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\desktop\assets\brenner.ico"; DestDir: "{app}"; DestName: "brenner.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\Barbearia Brenner"; Filename: "{app}\{#NomeExecutavel}"; WorkingDir: "{app}"; IconFilename: "{app}\brenner.ico"
Name: "{autodesktop}\Barbearia Brenner"; Filename: "{app}\{#NomeExecutavel}"; WorkingDir: "{app}"; IconFilename: "{app}\brenner.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#NomeExecutavel}"; Description: "Abrir Barbearia Brenner agora"; Flags: nowait postinstall skipifsilent

[Code]
const
  WebView2Guid = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function WebView2VersionExists(RootKey: Integer; const KeyPath: String): Boolean;
var
  VersionText: String;
begin
  Result := False;
  if RegQueryStringValue(RootKey, KeyPath, 'pv', VersionText) then
  begin
    Result := (VersionText <> '') and (VersionText <> '0.0.0.0');
  end;
end;

function IsWebView2Installed(): Boolean;
var
  PathSuffix: String;
begin
  PathSuffix := 'SOFTWARE\Microsoft\EdgeUpdate\Clients\' + WebView2Guid;
  // Aqui HKLM32 consulta a visão WOW6432Node em Windows x64.
  Result :=
    WebView2VersionExists(HKLM32, PathSuffix) or
    WebView2VersionExists(HKLM64, PathSuffix) or
    WebView2VersionExists(HKCU, PathSuffix);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  InstallerPath: String;
  ExitCode: Integer;
begin
  Result := '';
  if IsWebView2Installed() then
  begin
    Log('WebView2 Runtime existente; pulando instalação.');
    Exit;
  end;

  Log('WebView2 Runtime ausente. Iniciando instalação offline.');
  ExtractTemporaryFile('MicrosoftEdgeWebView2RuntimeInstallerX64.exe');
  InstallerPath := ExpandConstant('{tmp}\MicrosoftEdgeWebView2RuntimeInstallerX64.exe');

  if not Exec(InstallerPath, '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
  begin
    Result := 'Não foi possível iniciar a instalação do Microsoft WebView2. ' +
      SysErrorMessage(ExitCode);
    Exit;
  end;

  if ExitCode = 3010 then
  begin
    NeedsRestart := True;
    Result := 'O Microsoft WebView2 pediu reinicialização. Reinicie o computador e execute o instalador novamente.';
    Exit;
  end;

  if ExitCode <> 0 then
  begin
    Result := 'Falha na instalação do Microsoft WebView2 (código ' + IntToStr(ExitCode) + ').';
    Exit;
  end;

  if not IsWebView2Installed() then
    Result := 'O WebView2 terminou a instalação, mas não pôde ser detectado. Reinicie o Windows e tente novamente.';
end;
