<#
.SYNOPSIS
  Install the Employee Device Manager agent to start automatically at logon.

.DESCRIPTION
  Registers a per-user Scheduled Task that launches the agent (in supervise mode)
  when you sign in. This requires NO administrator rights and runs in your own
  user session, which is needed to read the foreground application.

  The task is fully visible: you can see and manage it in Task Scheduler and in
  Task Manager > Startup. This is deliberate - the agent is not hidden and does
  not use covert persistence.

.PARAMETER TaskName
  Name of the scheduled task (default: EmployeeDeviceManagerAgent).

.PARAMETER ConfigPath
  Path to config.json (default: config.json next to this script).
#>
param(
    [string]$TaskName = "EmployeeDeviceManagerAgent",
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$AgentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pythonw = Join-Path $AgentDir ".venv\Scripts\pythonw.exe"
$Runner = Join-Path $AgentDir "run_agent.py"
if (-not $ConfigPath) { $ConfigPath = Join-Path $AgentDir "config.json" }

if (-not (Test-Path $Pythonw)) {
    throw "Agent virtual environment not found at $Pythonw. Create it first: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}
if (-not (Test-Path $ConfigPath)) {
    throw "Config not found at $ConfigPath. Copy config.example.json to config.json and fill in the device id and enrollment secret."
}

$argument = "`"$Runner`" --config `"$ConfigPath`" --supervise"
$action = New-ScheduledTaskAction -Execute $Pythonw -Argument $argument -WorkingDirectory $AgentDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings `
    -Description "Employee Device Manager monitoring agent (user-level, visible)." `
    -Force | Out-Null

Write-Host "Installed logon task '$TaskName'."
Write-Host "The agent will start at your next sign-in (or run: Start-ScheduledTask -TaskName '$TaskName')."
Write-Host "It is visible in Task Scheduler and Task Manager > Startup. Remove it with: .\uninstall.ps1"
