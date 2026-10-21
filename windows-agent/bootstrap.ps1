<#
.SYNOPSIS
  One-command install of the Employee Device Manager agent on a Windows laptop.

.DESCRIPTION
  Downloads the agent (no git needed), sets up its Python environment, writes the
  config from the enrollment details, installs the auto-start logon task, and
  starts it. Requires Python 3.11+ to be installed.

  Easiest usage is the one-line command shown in the dashboard's "Add device"
  dialog, which fills in the values for you. Or run directly:

    powershell -ExecutionPolicy Bypass -File bootstrap.ps1 `
      -DeviceUid dev_xxx -Secret yyy -ServerUrl https://your-domain/api

.PARAMETER DeviceUid      Device id from the dashboard (dev_...).
.PARAMETER Secret         One-time enrollment secret from the dashboard.
.PARAMETER ServerUrl      Backend URL, e.g. https://your-domain/api
.PARAMETER InstallDir     Where to install (default: %LOCALAPPDATA%\TeraAgent).
#>
param(
    [string]$DeviceUid = $env:TERA_UID,
    [string]$Secret = $env:TERA_SECRET,
    [string]$ServerUrl = $env:TERA_URL,
    [string]$InstallDir = "$env:LOCALAPPDATA\TeraAgent",
    [string]$TaskName = "EmployeeDeviceManagerAgent",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

if (-not $DeviceUid -or -not $Secret -or -not $ServerUrl) {
    throw "Missing details. Provide -DeviceUid, -Secret and -ServerUrl (or set TERA_UID / TERA_SECRET / TERA_URL). The dashboard's Add device dialog gives you the ready-made command."
}

# 1. Python must be present.
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    throw "Python is not installed. Install it first, then re-run this command:`n  winget install -e --id Python.Python.3.12`nor download from https://python.org (tick 'Add Python to PATH')."
}

Write-Host "Downloading the agent..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$zip = Join-Path $env:TEMP "tera-agent.zip"
$extract = Join-Path $env:TEMP "tera-extract"
Invoke-WebRequest -Uri "https://github.com/Giddymaster/Tera/archive/refs/heads/$Branch.zip" -OutFile $zip
if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }
Expand-Archive -Path $zip -DestinationPath $extract -Force
Copy-Item -Recurse -Force (Join-Path $extract "Tera-$Branch\windows-agent\*") $InstallDir

Set-Location $InstallDir

Write-Host "Setting up the Python environment (first run takes a minute)..."
python -m venv .venv
& "$InstallDir\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$InstallDir\.venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt

Write-Host "Writing configuration..."
$config = [ordered]@{
    server_url                    = $ServerUrl
    device_uid                    = $DeviceUid
    enrollment_secret             = $Secret
    heartbeat_interval_seconds    = 60
    usage_flush_interval_seconds  = 120
    sample_interval_seconds       = 5
}
$config | ConvertTo-Json | Set-Content -Path (Join-Path $InstallDir "config.json") -Encoding utf8
# Clear any previous enrollment so it enrolls fresh against this server.
Remove-Item -ErrorAction SilentlyContinue (Join-Path $InstallDir ".agent_state.json")

Write-Host "Installing auto-start task and starting the agent..."
& powershell -ExecutionPolicy Bypass -File (Join-Path $InstallDir "install.ps1") -TaskName $TaskName
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "Done. This device should appear Online in the dashboard within a minute."
Write-Host "Installed at: $InstallDir   (remove later with: $InstallDir\uninstall.ps1)"
