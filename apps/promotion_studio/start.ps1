$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if (-not $command) {
        Write-Error "Python 3.11+ was not found. Create .venv and install requirements-dev.txt first."
        exit 1
    }
    $python = $command.Source
    Write-Host "Using system Python: $python"
    Write-Host "For a clean setup: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

$data = Join-Path $root "local-data"
Push-Location $root
try {
    & $python -X utf8 main.py --serve --port 8080 --data $data
}
finally {
    Pop-Location
}
