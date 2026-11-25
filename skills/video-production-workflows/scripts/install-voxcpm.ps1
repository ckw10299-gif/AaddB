[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'VideoProductionTools\VoxCPM'),
    [ValidateSet('auto','cpu','cuda')][string]$Device = 'auto',
    [string]$TorchIndexUrl,
    [string]$Revision,
    [string]$ModelPath,
    [ValidateRange(1024,65535)][int]$Port = 8808,
    [switch]$PlanOnly
)
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/OpenBMB/VoxCPM.git'
$defaultModel = 'openbmb/VoxCPM2'
$InstallDir = [IO.Path]::GetFullPath($InstallDir)
if ($TorchIndexUrl -and $TorchIndexUrl -notmatch '^https://download\.pytorch\.org/whl/(?:cpu|cu\d+)/?$') {
    throw 'TorchIndexUrl must be an official PyTorch CPU or CUDA wheel index.'
}
if ($TorchIndexUrl -match '/cpu/?$' -and $Device -eq 'cuda') {
    throw 'The CPU wheel index cannot be used with -Device cuda.'
}
if ($Revision -and $Revision -notmatch '^[A-Za-z0-9][A-Za-z0-9._/-]*$') {
    throw 'Revision must be a Git tag, branch, or commit identifier.'
}
if ($ModelPath) { $ModelPath = [IO.Path]::GetFullPath($ModelPath) }
$model = if ($ModelPath) { $ModelPath } else { $defaultModel }
$launcher = Join-Path $InstallDir 'Start-VoxCPM.cmd'
Write-Output "Repository: $repo"
Write-Output "Installation: $InstallDir"
Write-Output "Model: $model ; device: $Device ; local port: $Port"
if ($PlanOnly) {
    Write-Output 'Plan only: check Python and Git; clone if absent; prepare .venv; verify dependencies and device; render a WAV; create local launcher. No changes made.'
    return
}

function Invoke-Checked([string]$Exe, [string[]]$Argv) {
    & $Exe @Argv
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE ($($Argv[0]))." }
}

function Install-WinGet([string]$Package) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (!$winget) { throw "Missing prerequisite $Package and winget is unavailable. Install the prerequisite using its official installer, then retry." }
    Invoke-Checked $winget.Source @('install','--id',$Package,'--exact','--source','winget','--accept-package-agreements','--accept-source-agreements','--disable-interactivity')
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ';' + $env:Path
}

function Get-Python311 {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $resolved = & $py.Source -3.11 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved -and (Test-Path -LiteralPath $resolved -PathType Leaf)) { return $resolved }
    }
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
        (Join-Path $env:ProgramFiles 'Python311\python.exe')
    )
    if ($cmd -and $cmd.Source -notmatch '\\WindowsApps\\') { $candidates += $cmd.Source }
    foreach ($entry in $candidates) {
        if (Test-Path -LiteralPath $entry -PathType Leaf) {
            & $entry -c "import sys; raise SystemExit(sys.version_info[:2] != (3,11))" 2>$null
            if ($LASTEXITCODE -eq 0) { return $entry }
        }
    }
}

if ($ModelPath -and !(Test-Path -LiteralPath (Join-Path $ModelPath 'model.safetensors') -PathType Leaf)) {
    throw "No model.safetensors found at $ModelPath. Supply a complete VoxCPM2 snapshot or omit -ModelPath."
}
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if (!$git) {
    Install-WinGet 'Git.Git'
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if (!$git) { throw 'Git installation completed but git.exe is not visible; open a new terminal and retry.' }
}
if (Test-Path -LiteralPath $InstallDir) {
    if (!(Test-Path -LiteralPath (Join-Path $InstallDir '.git'))) { throw "Refusing to install into an existing non-Git directory: $InstallDir" }
    $origin = & $git.Source -C $InstallDir remote get-url origin
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch '^https://github\.com/OpenBMB/VoxCPM(?:\.git)?/?$') {
        throw "Existing project does not identify the official VoxCPM origin: $InstallDir"
    }
    if ($Revision) { throw 'Revision can only be selected in a fresh directory. Existing checkouts are never changed automatically.' }
} else {
    New-Item -ItemType Directory -Path (Split-Path -Parent $InstallDir) -Force | Out-Null
    Invoke-Checked $git.Source @('clone',$repo,$InstallDir)
    if ($Revision) { Invoke-Checked $git.Source @('-C',$InstallDir,'checkout','--detach',$Revision) }
}

$venv = Join-Path $InstallDir '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $venv -PathType Leaf)) {
    $python = Get-Python311
    if (!$python) { Install-WinGet 'Python.Python.3.11'; $python = Get-Python311 }
    if (!$python) { throw 'Python 3.11 not found after installation; reopen PowerShell and retry.' }
    Invoke-Checked $python @('-m','venv',(Join-Path $InstallDir '.venv'))
}

Push-Location -LiteralPath $InstallDir
try {
    & $venv -c "import voxcpm, torch, soundfile" 2>$null
    $hasRuntime = $LASTEXITCODE -eq 0
    if (!$hasRuntime) {
        if ($Device -eq 'cuda' -and !$TorchIndexUrl) { throw 'For a fresh CUDA installation, supply -TorchIndexUrl from the official PyTorch selector.' }
        if ($Device -eq 'cpu' -and !$TorchIndexUrl) { $TorchIndexUrl = 'https://download.pytorch.org/whl/cpu' }
        Invoke-Checked $venv @('-m','pip','install','--upgrade','pip')
        if ($TorchIndexUrl) {
            Invoke-Checked $venv @('-m','pip','install','torch','torchaudio','--index-url',$TorchIndexUrl)
        }
        Invoke-Checked $venv @('-m','pip','install','-e','.')
    }
    Invoke-Checked $venv @('-m','pip','check')
    $env:HF_HOME = Join-Path $InstallDir 'models\huggingface'
    $env:MODELSCOPE_CACHE = Join-Path $InstallDir 'models\modelscope'
    Write-Output 'Starting a real synthesis test. First run may download the model.'
    $wav = Join-Path $InstallDir ('voxcpm-smoke-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.wav')
    Invoke-Checked $venv @((Join-Path $PSScriptRoot 'smoke_voxcpm.py'),'--model',$model,'--device',$Device,'--output',$wav)
    if (!(Test-Path -LiteralPath $launcher)) {
        $modelArg = if ($ModelPath) { ' --model-id "' + $ModelPath.Replace('%','%%') + '"' } else { '' }
        $lines = @('@echo off','chcp 65001 >nul','cd /d "%~dp0"','set "HF_HOME=%~dp0models\huggingface"','set "MODELSCOPE_CACHE=%~dp0models\modelscope"',"echo Open http://127.0.0.1:$Port/ in your browser.", ('"%~dp0.venv\Scripts\python.exe" "%~dp0app.py" --host 127.0.0.1 --port ' + $Port + ' --device ' + $Device + $modelArg),'pause')
        [IO.File]::WriteAllLines($launcher, $lines, [Text.UTF8Encoding]::new($false))
    } else {
        Write-Output 'Existing launcher retained. Its port/device settings may differ from this run.'
    }
    Invoke-Checked $git.Source @('-C',$InstallDir,'rev-parse','HEAD')
    Write-Output "Verified WAV: $wav"
    Write-Output "Launcher: $launcher"
} finally {
    Pop-Location
}
