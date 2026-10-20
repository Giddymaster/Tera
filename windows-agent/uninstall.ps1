<#
.SYNOPSIS
  Remove the Employee Device Manager agent's logon task.

.DESCRIPTION
  Stops and unregisters the scheduled task created by install.ps1. Optionally
  purges the stored device token so the device would need to be re-enrolled.

.PARAMETER TaskName
  Name of the scheduled task (default: EmployeeDeviceManagerAgent).

.PARAMETER Purge
  Also delete the stored device token (.agent_state.json).
#>
param(
    [string]$TaskName = "EmployeeDeviceManagerAgent",
    [switch]$Purge
)

$ErrorActionPreference = "Stop"
$AgentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    try { Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue } catch {}
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed logon task '$TaskName'."
} else {
    Write-Host "No task named '$TaskName' was found."
}

if ($Purge) {
    $state = Join-Path $AgentDir ".agent_state.json"
    if (Test-Path $state) {
        Remove-Item $state -Force
        Write-Host "Purged stored device token (.agent_state.json). Re-enrollment will be required."
    }
}
