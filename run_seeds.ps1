<#
.SYNOPSIS
Run a seeds file through the Probe seed runner with safe defaults.

.PARAMETER File
Path to a seed file (required).

.PARAMETER Limit
Limit number of seeds to process (default: 5).

.PARAMETER Ingest
Switch to persist fetched results into the DB.

.PARAMETER Db
Database file path (default: probe.db).

.PARAMETER Timeout
HTTP timeout in seconds (default: 10).

.PARAMETER MaxRetries
Maximum retry attempts for transient errors (default: 3).

.PARAMETER BackoffFactor
Backoff factor in seconds (default: 0.5).

.PARAMETER DryRun
Perform a dry-run (no ingest), present what would be executed.

.EXAMPLE
.
PS> .\run_seeds.ps1 -File seeds/test_simple.txt -Limit 5 -Ingest -Db myprobe.db

Runs the first 5 seeds from the file and ingests successful fetches into myprobe.db.
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$File,

    [int]$Limit = 5,
    [switch]$Ingest,
    [string]$DbPath = "probe.db",
    [double]$Timeout = 10,
    [int]$MaxRetries = 3,
    [double]$BackoffFactor = 0.5,
    [switch]$DryRun
)

# Ensure script runs from repo root (where cli.py is located)
Set-Location -Path $PSScriptRoot

if (-not (Test-Path $File)) {
    Write-Error "Seed file not found: $File"
    exit 2
}

# Build argument list
$argsList = @('cli.py', 'seeds', 'run', $File, '--limit', $Limit.ToString(), '--db', $DbPath, '--timeout', $Timeout.ToString(), '--max-retries', $MaxRetries.ToString(), '--backoff-factor', $BackoffFactor.ToString())
if ($Ingest.IsPresent -and -not $DryRun.IsPresent) { $argsList += '--ingest' }

$cmd = "python " + ($argsList -join ' ')

if ($DryRun.IsPresent) {
    Write-Host "DRY-RUN: $cmd"
    exit 0
}

Write-Host "Running: $cmd"

try {
    & python @argsList
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        Write-Error "Command exited with code $exit"
        exit $exit
    }
} catch {
    Write-Error "Execution failed: $_"
    exit 1
}

Write-Host "Done."
