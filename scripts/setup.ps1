# Setup en Windows (PowerShell): crea venv, instala el paquete y corre un smoke test.
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot

Write-Host "==> Creando entorno virtual (.venv)..." -ForegroundColor Cyan
python -m venv "$raiz\.venv"
& "$raiz\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$raiz\.venv\Scripts\python.exe" -m pip install -e "$raiz"

Write-Host "==> Verificando conversion PDF->HTML (sin LLM)..." -ForegroundColor Cyan
& "$raiz\.venv\Scripts\python.exe" -m rca.cli run-all --no-llm

Write-Host ""
Write-Host "Listo. Siguientes pasos:" -ForegroundColor Green
Write-Host "  1) Instala Ollama:  https://ollama.com/download"
Write-Host "  2) Descarga el modelo:  ollama pull qwen2.5:3b-instruct"
Write-Host "  3) Corre el pipeline:  .\.venv\Scripts\python.exe -m rca.cli run-all"
