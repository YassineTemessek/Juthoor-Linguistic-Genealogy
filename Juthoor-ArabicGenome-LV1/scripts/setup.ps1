param(
  [string]$Python = "python",
  [switch]$IngestDeps
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  & $Python -m venv .venv
}

$pip = Join-Path ".venv" "Scripts\\pip.exe"

& $pip install --upgrade pip

if (Test-Path "requirements.txt") {
  & $pip install -r requirements.txt
}

if ($IngestDeps) {
  & $pip install -r requirements-ingest.txt
}

Write-Host "OK. Activate with: .\\.venv\\Scripts\\Activate.ps1"

