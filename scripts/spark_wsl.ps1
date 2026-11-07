<#
.SYNOPSIS
    Spark in WSL for audio_features: check the toolchain, set it up, verify it, run uv there.

.DESCRIPTION
    WSL is the BUILD host. Windows Spark has no winutils.exe / hadoop.dll, so it parses and
    computes but cannot write Parquet or create a Hive database (/spark-env, "Windows
    capability honesty"); Windows is for debugging, `dbt parse` and `dbt compile`, and every
    `dbt build` runs in WSL through -Run.

    This script is the Windows entry point. All Linux logic lives in
    scripts/spark_wsl_bootstrap.sh -- bash inside PowerShell string literals is where these
    scripts go to die, and a standalone .sh is testable from inside WSL on its own.

    It is NOT a package manager. -Setup installs uv if missing, fetches CPython 3.11 through
    uv and runs `uv sync --frozen` into ~/.venvs/audio-features (outside the repo, so the
    Windows .venv is never rebuilt). It writes nothing to ~/.profile or ~/.bashrc.

.PARAMETER Check
    Report the state of the WSL toolchain. Changes nothing. This is the default.

.PARAMETER Setup
    Make the toolchain ready. Idempotent -- safe to re-run any time (after `uv lock` on Windows).

.PARAMETER Verify
    Known-answer probe: prove Spark COMPUTES CORRECTLY and WRITES in WSL, not merely that a
    session starts. Group-by, a Python UDF, a Parquet write and a Hive CTAS, compared to
    constants.

.PARAMETER Run
    Run `uv run <Run>` in the repo under WSL, in the WSL venv. The string is passed whole.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\spark_wsl.ps1 -Check
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\spark_wsl.ps1 -Setup
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\spark_wsl.ps1 -Verify
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\spark_wsl.ps1 -Run "dbt build --target dev"
#>
[CmdletBinding(DefaultParameterSetName = 'Check')]
param(
    [Parameter(ParameterSetName = 'Check')]  [switch] $Check,
    [Parameter(ParameterSetName = 'Setup')]  [switch] $Setup,
    [Parameter(ParameterSetName = 'Verify')] [switch] $Verify,
    [Parameter(ParameterSetName = 'Run')]    [string] $Run,
    [string] $Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

# Output from processes we run INSIDE the distro is UTF-8. (wsl.exe's OWN subcommands --
# --list, --status -- emit UTF-16LE, which under PS 5.1 comes back riddled with nulls. This
# script never parses those; see Test-Distro.)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Test-Distro {
    # Exit-code probe rather than parsing `wsl --list`. Also starts the distro if it was
    # Stopped, which is exactly what we want.
    & wsl.exe -d $Distro -e true 2>$null
    return ($LASTEXITCODE -eq 0)
}

function ConvertTo-WslPath([string] $WinPath) {
    # -e bypasses the login shell so backslashes reach wslpath intact.
    return (& wsl.exe -d $Distro -e wslpath -a "$WinPath")
}

function Invoke-Bootstrap([string] $Verb, [string] $CmdB64 = '') {
    # Out-Host, not bare output: in PowerShell a function returns EVERYTHING it emits, so
    # `$rc = Invoke-Bootstrap 'check'` would capture the whole report into $rc and the user
    # would see nothing. Push it to the host and return only the exit code.
    #
    # PS 5.1 wraps a native command's stderr in ErrorRecords, so with 'Stop' a tool that logs
    # progress to stderr (uv, java, spark) can kill the script on exit 0. Gate on
    # $LASTEXITCODE instead and relax the preference just for this call.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & wsl.exe -d $Distro -e env `
            "SPARK_WSL_REPO=$script:RepoLinux" `
            "SPARK_WSL_CMD_B64=$CmdB64" `
            bash $script:BootstrapLinux $Verb | Out-Host
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
}

if (-not (Test-Distro)) {
    Write-Host "WSL distro '$Distro' did not start." -ForegroundColor Red
    Write-Host "  wsl --list --verbose     # what is installed"
    Write-Host "  wsl --install -d Ubuntu  # if there is nothing there"
    exit 1
}

$RepoWin   = Split-Path $PSScriptRoot -Parent
$RepoLinux = ConvertTo-WslPath $RepoWin
$BootstrapLinux = ConvertTo-WslPath (Join-Path $PSScriptRoot 'spark_wsl_bootstrap.sh')
$user = (& wsl.exe -d $Distro -e id -un)

switch ($PSCmdlet.ParameterSetName) {

    'Setup' {
        $rc = Invoke-Bootstrap 'ensure'
        exit $rc
    }

    'Verify' {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $lines = & wsl.exe -d $Distro -e env "SPARK_WSL_REPO=$RepoLinux" bash $BootstrapLinux verify
        $ErrorActionPreference = $prev
        # The JSON is the last line that starts with '{'; anything before it is Spark noise.
        $json = @($lines | Where-Object { $_ -is [string] -and $_.StartsWith('{') })[-1]
        Write-Host $json
        try { $r = $json | ConvertFrom-Json } catch { Write-Host "unparseable output" -ForegroundColor Red; exit 1 }
        if ($r.ok) {
            Write-Host ("VERIFIED - spark {0} on python {1}, java {2}: group-by, UDF, Parquet write and Hive CTAS all correct." -f `
                        $r.spark, $r.python, $r.java) -ForegroundColor Green
            exit 0
        }
        Write-Host "FAILED - Spark in WSL did not produce the expected answers." -ForegroundColor Red
        if ($r.error) { Write-Host "  $($r.error)" }
        exit 1
    }

    'Run' {
        if (-not $Run) { Write-Host "-Run needs a command line, e.g. -Run 'dbt build --target dev'" -ForegroundColor Yellow; exit 2 }
        # Base64 across the shell boundary: PS 5.1 does not escape embedded double quotes when
        # it hands arguments to a native command, so a `python -c "..."` payload would arrive
        # torn. The .sh decodes and word-splits it itself.
        $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Run))
        Write-Host "uv run $Run   (WSL: $Distro, user $user, repo $RepoLinux)"
        $rc = Invoke-Bootstrap 'run' $b64
        exit $rc
    }

    default {
        Write-Host "distro   $Distro (user $user)"
        Write-Host "repo     $RepoLinux"
        Write-Host ""
        $rc = Invoke-Bootstrap 'check'
        exit $rc
    }
}
