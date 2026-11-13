# $ErrorActionPreference = 'Stop'
# Set-Location (Join-Path $PSScriptRoot '..')
# if (-not (Test-Path 'frontend\dist\admin\index.html')) { throw 'Compile o frontend antes: cd frontend; npm run build:desktop' }
# if (-not (Test-Path 'frontend\dist\barbearia\index.html')) { throw 'Faltou o HTML de barbearia no build.' }
# python -m pip install -r desktop\requirements.txt
# python -m PyInstaller --clean --noconfirm --onefile --windowed --name BrennerDesktop --collect-all webview --add-data 'frontend\dist;frontend\dist' --add-data 'desktop\config.example.json;desktop' --add-data 'desktop\selecionar.html;desktop' desktop\launcher.py
# Write-Host 'Gerado: dist\BrennerDesktop.exe'
$ErrorActionPreference = 'Stop'

# Raiz do projeto
Set-Location (Join-Path $PSScriptRoot '..')

# Verificar arquivos do React
if (-not (Test-Path 'frontend\dist\admin\index.html')) {
    throw 'Compile o frontend: cd frontend; npm run build:desktop'
}

if (-not (Test-Path 'frontend\dist\barbearia\index.html')) {
    throw 'HTML do balcao nao encontrado.'
}

# Icone oficial da Barbearia Brenner
$icone = 'desktop\assets\brenner.ico'

if (-not (Test-Path $icone)) {
    throw "Icone nao encontrado: $icone"
}

Write-Host 'Icone encontrado:' (Resolve-Path $icone)

# Dependencias
python -m pip install -r desktop\requirements.txt

if ($LASTEXITCODE -ne 0) {
    throw 'Falha na instalacao das dependencias.'
}

# Compilar executavel
python -m PyInstaller `
    --clean `
    --noconfirm `
    --onefile `
    --windowed `
    --name BrennerDesktop `
    --icon "$icone" `
    --paths "." `
    --collect-all webview `
    --add-data "frontend\dist;frontend\dist" `
    --add-data "desktop\config.example.json;desktop" `
    --add-data "desktop\selecionar.html;desktop" `
    --add-data "desktop\assets\brenner.ico;desktop\assets" `
    desktop\launcher.py

if ($LASTEXITCODE -ne 0) {
    throw 'Erro na compilacao do aplicativo.'
}

Write-Host ''
Write-Host '========================================'
Write-Host '  BARBEARIA BRENNER - COMPILADO'
Write-Host '========================================'
Write-Host 'Executavel: dist\BrennerDesktop.exe'
Write-Host 'Icone: Coroa Brenner'