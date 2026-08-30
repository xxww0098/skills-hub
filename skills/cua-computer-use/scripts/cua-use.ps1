#!/usr/bin/env pwsh
# cua-use.ps1 — Windows skill CLI for Cua Computer Use 2.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SkillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:Path = "$env:USERPROFILE\.local\bin;$env:LOCALAPPDATA\cua-driver;$env:Path"

function Die([string]$Message) {
    Write-Error "cua-use: $Message"
    exit 1
}

function Info([string]$Message) {
    Write-Host "cua-use: $Message" -ForegroundColor DarkGray
}

function Usage {
    @"
Usage: cua-use.ps1 <command> [args...]

Host desktop (Cua Driver) — default:
  ensure                         Install if missing, start daemon, probe list_apps
  install                        Official installer
  bin                            Print cua-driver path
  doctor / status
  serve                          Start daemon
  call <tool> [json]             Invoke a driver tool
  list-tools / describe <tool>
  connect [client]               skills install + print MCP config
  skills [install|status]
  mcp-config [--client NAME]
  update / telemetry-disable

Isolated sandbox:
  sandbox-install                pip install cua
  sandbox-smoke

Passthrough:
  -- <args...>                   Raw cua-driver args
"@
}

function Resolve-Driver {
    if ($env:CUA_DRIVER_BIN -and (Test-Path $env:CUA_DRIVER_BIN)) {
        return $env:CUA_DRIVER_BIN
    }
    $cmd = Get-Command cua-driver -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($cand in @(
            "$env:USERPROFILE\.local\bin\cua-driver.exe",
            "$env:USERPROFILE\.local\bin\cua-driver",
            "$env:LOCALAPPDATA\cua-driver\cua-driver.exe"
        )) {
        if (Test-Path $cand) { return $cand }
    }
    return $null
}

function Install-Driver {
    Info "installing cua-driver via https://cua.ai/driver/install.ps1"
    Invoke-Expression (Invoke-RestMethod https://cua.ai/driver/install.ps1)
    $bin = Resolve-Driver
    if (-not $bin) { Die "install finished but cua-driver is not on PATH. Open a new PowerShell." }
    return $bin
}

function Invoke-Driver {
    $bin = Resolve-Driver
    if (-not $bin) { Die "cua-driver not found. Run: cua-use.ps1 install" }
    & $bin @args
}

function Test-Daemon([string]$Bin) {
    & $Bin call list_apps 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Start-Daemon([string]$Bin) {
    Start-Process -FilePath $Bin -ArgumentList "serve" -WindowStyle Hidden
}

function Wait-Daemon([string]$Bin) {
    for ($i = 0; $i -lt 10; $i++) {
        if (Test-Daemon $Bin) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Cmd-Ensure {
    $bin = Resolve-Driver
    if (-not $bin) { $bin = Install-Driver }
    if (-not (Test-Daemon $bin)) {
        Info "starting cua-driver daemon"
        Start-Daemon $bin
        if (-not (Wait-Daemon $bin)) {
            & $bin doctor
            Die "daemon not ready. Must run in an interactive user session (not Session 0)."
        }
    }
    & $bin --version
    & $bin call list_apps
}

function Cmd-Connect([string]$Client) {
    Invoke-Driver skills install
    if ($Client -and $Client -ne "generic") {
        Invoke-Driver mcp-config --client $Client
    } else {
        Invoke-Driver mcp-config
    }
    Invoke-Driver skills status
}

$cmd = if ($args.Count -ge 1) { $args[0] } else { "" }
$rest = @()
if ($args.Count -gt 1) { $rest = $args[1..($args.Count - 1)] }

switch ($cmd) {
    { $_ -in @("", "-h", "--help") } { Usage; exit 0 }
    "ensure" { Cmd-Ensure }
    "install" { Install-Driver }
    "bin" {
        $b = Resolve-Driver
        if (-not $b) { Die "cua-driver not found" }
        Write-Output $b
    }
    "doctor" { Invoke-Driver doctor @rest }
    "status" { Invoke-Driver status @rest }
    "serve" {
        $bin = Resolve-Driver
        if (-not $bin) { Die "install first" }
        Start-Daemon $bin
        if (-not (Wait-Daemon $bin)) { Die "daemon failed to start" }
        Info "daemon ready"
    }
    "call" {
        if ($rest.Count -lt 1) { Die "usage: cua-use.ps1 call <tool> [json]" }
        Invoke-Driver call @rest
    }
    "list-tools" { Invoke-Driver list-tools @rest }
    "describe" { Invoke-Driver describe @rest }
    "connect" {
        $client = if ($rest.Count -ge 1) { $rest[0] } else { "generic" }
        Cmd-Connect $client
    }
    "skills" {
        $sub = if ($rest.Count -ge 1) { $rest[0] } else { "status" }
        $more = @()
        if ($rest.Count -gt 1) { $more = $rest[1..($rest.Count - 1)] }
        Invoke-Driver skills $sub @more
    }
    "mcp-config" { Invoke-Driver mcp-config @rest }
    "update" { Invoke-Driver update --apply @rest }
    "telemetry-disable" { Invoke-Driver telemetry disable }
    "sandbox-install" { python -m pip install -U cua }
    "sandbox-smoke" {
        python -c @"
import asyncio
from cua import Sandbox, Image
async def main():
    async with Sandbox.ephemeral(Image.linux(), local=True) as sb:
        r = await sb.shell.run('echo hello')
        print(getattr(r, 'stdout', r))
        await sb.screenshot()
        print('sandbox smoke: ok')
asyncio.run(main())
"@
    }
    "--" { Invoke-Driver @rest }
    default {
        $bin = Resolve-Driver
        if ($bin) {
            Invoke-Driver call $cmd @rest
        } else {
            Usage
            Die "unknown command '$cmd'"
        }
    }
}
