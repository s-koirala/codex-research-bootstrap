# Thin PowerShell wrapper for tools/install.py.
# Locates a Python >= 3.10 interpreter and execs the installer.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Installer = Join-Path $PSScriptRoot 'tools/install.py'
if (-not (Test-Path -LiteralPath $Installer)) {
    Write-Error "install.ps1: cannot find $Installer"
    exit 2
}

function Test-PythonOk {
    param([string]$Exe, [string[]]$Prefix = @())
    try {
        # $pyArgs avoids shadowing PowerShell's $args automatic variable inside the function scope.
        $pyArgs = $Prefix + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)')
        & $Exe @pyArgs 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

$PythonCmd = $null
foreach ($candidate in @('python.exe', 'python')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        if (Test-PythonOk -Exe $candidate) { $PythonCmd = @($candidate); break }
    }
}
if (-not $PythonCmd -and (Get-Command 'py' -ErrorAction SilentlyContinue)) {
    if (Test-PythonOk -Exe 'py' -Prefix @('-3')) { $PythonCmd = @('py', '-3') }
}

if (-not $PythonCmd) {
    Write-Error "install.ps1: no Python >= 3.10 found (tried: python.exe, python, py -3)"
    exit 1
}

# Flags are passed through verbatim using POSIX style (--dry-run, --force, --scope user, etc).
# StrictMode-safe slice: $PythonCmd[1..($Length-1)] degenerates to [1,0] on a 1-element array,
# which throws under Set-StrictMode Latest. Build the splat conditionally instead.
$ExtraArgs = @()
if ($PythonCmd.Length -gt 1) { $ExtraArgs = $PythonCmd[1..($PythonCmd.Length - 1)] }
& $PythonCmd[0] @($ExtraArgs + @($Installer) + $args)
exit $LASTEXITCODE
