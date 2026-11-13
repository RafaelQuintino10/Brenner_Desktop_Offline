<#
  Executar NA RAIZ do projeto: .\installer\CRIAR_INSTALADOR.ps1
  Pré-requisitos da MÁQUINA DESENVOLVEDORA: Python 3 x64, Node.js, Inno Setup 6.3+
  O computador do cliente NÃO precisa dessas ferramentas.
  Requer redist\MicrosoftEdgeWebView2RuntimeInstallerX64.exe (Evergreen Standalone x64 oficial).
#>
param(
    [switch]$PularBuildReact,
    [switch]$PularInstalacaoPacotes,
    [switch]$PularBuildPython
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

function Assert-File([string]$file, [string]$message) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw $message }
}
function Check-Exit([string]$action) {
    if ($LASTEXITCODE -ne 0) { throw "$action falhou (código $LASTEXITCODE)." }
}

Write-Host "`n=== BARBEARIA BRENNER — INSTALADOR OFFLINE ===" -ForegroundColor Yellow
Assert-File 'desktop\launcher.py' 'Execute o script na raiz do seu projeto desktop (pasta desktop/ ausente).'
Assert-File 'desktop\assets\brenner.ico' 'Faltou desktop\assets\brenner.ico. Copie o arquivo do kit.'
Assert-File 'frontend\package.json' 'Frontend React não encontrado.'

# Requisito de instalação 100% offline para o computador do cliente.
$webview = 'installer\redist\MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
Assert-File $webview "Falta o WebView2 Standalone x64! Baixe em https://developer.microsoft.com/en-us/microsoft-edge/webview2/ e salve como $webview"
$size = (Get-Item $webview).Length
if ($size -lt 10MB) { throw 'O arquivo WebView2 é pequeno demais: use o Evergreen STANDALONE x64, não o Bootstrapper online.' }
$signature = Get-AuthenticodeSignature -FilePath $webview
if ($signature.Status -ne 'Valid' -or ($signature.SignerCertificate.Subject -notmatch 'Microsoft')) {
    throw 'A assinatura Microsoft do WebView2 não foi validada. Baixe novamente do site oficial.'
}
Write-Host 'WebView2 standalone x64 verificado e assinado pela Microsoft.' -ForegroundColor Green

if (-not $PularBuildReact) {
    Write-Host "`n[1/3] Compilando o React desktop..." -ForegroundColor Cyan
    Push-Location 'frontend'
    try {
        if (-not (Test-Path 'node_modules')) {
            & npm.cmd ci
            Check-Exit 'npm ci'
        }
        & npm.cmd run build:desktop
        Check-Exit 'npm run build:desktop'
    }
    finally { Pop-Location }
}
Assert-File 'frontend\dist\admin\index.html' 'Faltou dist/admin/index.html. Rode npm run build:desktop.'
Assert-File 'frontend\dist\barbearia\index.html' 'Faltou dist/barbearia/index.html. Rode npm run build:desktop.'

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host "`nCriando ambiente virtual local (.venv)..." -ForegroundColor Cyan
    & py -3 -m venv '.venv'
    Check-Exit 'Criação da venv Python'
}
Assert-File $python 'Python da .venv não encontrado.'
# & $python -c 'import platform,struct; assert struct.calcsize("P") * 8 == 64, "Python precisa ser 64 bits"; assert platform.system() == "Windows", "Compile no Windows"'
# Check-Exit 'Verificação Python x64'
& $python -c 'import sys; assert sys.maxsize > 2**32'
Check-Exit 'Verificação Python x64'

if (-not $PularInstalacaoPacotes) {
    Write-Host "`nAtualizando as dependências de build..." -ForegroundColor Cyan
    & $python -m pip install -r 'desktop\requirements.txt'
    Check-Exit 'pip install requirements'
}
# & $python -c 'import webview, PyInstaller; print("pywebview e PyInstaller encontrados")'
# Check-Exit 'Verificação das dependências Python'
& $python -c 'import webview, PyInstaller'
Check-Exit 'Verificação das dependências Python'

Write-Host 'pywebview e PyInstaller encontrados.' -ForegroundColor Green

if (-not $PularBuildPython) {
    Write-Host "`n[2/3] Empacotando Python + React (PyInstaller --onedir)..." -ForegroundColor Cyan
    $argsPI = @(
        '-m', 'PyInstaller', '--clean', '--noconfirm',
        '--onedir', '--windowed', '--name', 'BrennerDesktop',
        '--paths', '.', '--collect-all', 'webview',
        '--hidden-import', 'clr',
        '--icon', 'desktop\assets\brenner.ico',
        '--add-data', 'frontend\dist;frontend\dist',
        '--add-data', 'desktop\config.example.json;desktop',
        '--add-data', 'desktop\selecionar.html;desktop',
        '--add-data', 'desktop\assets\brenner.ico;desktop\assets',
        'desktop\launcher.py'
    )
    & $python @argsPI
    Check-Exit 'PyInstaller'
}
Assert-File 'dist\BrennerDesktop\BrennerDesktop.exe' 'O executável PyInstaller não foi encontrado.'

Write-Host "`n[3/3] Compilando o instalador com Inno Setup..." -ForegroundColor Cyan
$isccCmd = Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue
$iscc = if ($isccCmd) { $isccCmd.Source } else { $null }
if (-not $iscc) {
    $pf86 = [Environment]::GetFolderPath('ProgramFilesX86')
    $pf = [Environment]::GetFolderPath('ProgramFiles')
    foreach ($candidate in @(
        # (Join-Path $pf86 'Inno Setup 6\ISCC.exe'),
        # (Join-Path $pf 'Inno Setup 6\ISCC.exe')
        (Join-Path $pf 'Inno Setup 7\ISCC.exe'),
        (Join-Path $pf86 'Inno Setup 7\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
        (Join-Path $pf86 'Inno Setup 6\ISCC.exe'),
        (Join-Path $pf 'Inno Setup 6\ISCC.exe')
    )) {
        if (Test-Path $candidate) { $iscc = $candidate; break }
    }
}
if (-not $iscc) {
    throw 'Inno Setup 6 não encontrado. Instale com: winget install --id JRSoftware.InnoSetup -e -s winget'
}
& $iscc 'installer\BarbeariaBrenner.iss'
Check-Exit 'Inno Setup ISCC'

$output = Join-Path $root 'dist_instalador\Barbearia_Brenner_Setup_1.0.0_x64.exe'
Assert-File $output 'Instalador compilado, mas não foi localizado no diretório esperado.'
Write-Host "`nINSTALADOR PRONTO: $output" -ForegroundColor Green
Write-Host 'Distribua SOMENTE o Setup gerado. Teste primeiro numa VM Windows limpa.' -ForegroundColor Green
