# =====================================================================
#  Arranque en el OTRO PC (Windows / PowerShell).
#  Hace TODO de una: venv -> instalar -> verificar Ollama -> modelo -> correr.
#
#  Uso (desde la carpeta del repo, tras clonar):
#     powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#  Opciones:
#     -Modelo "qwen2.5:7b-instruct"   # usar otro modelo (PC con 16GB+)
#     -NoLlm                          # solo convertir+segmentar, sin IA
# =====================================================================
param(
    [string]$Modelo = "qwen2.5:3b-instruct",
    [switch]$NoLlm
)
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $raiz ".venv\Scripts\python.exe"

function Tiene($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# --- 1) Entorno virtual + instalación ---
if (-not (Test-Path $venvPy)) {
    Write-Host "==> Creando entorno virtual (.venv)..." -ForegroundColor Cyan
    $py = if (Tiene "python") { "python" } elseif (Tiene "py") { "py -3" } else { throw "No se encontró Python. Instala Python 3.10+ y reabre PowerShell." }
    & cmd /c "$py -m venv `"$raiz\.venv`""
}
Write-Host "==> Instalando dependencias..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -e $raiz

# --- 2) Si pidieron sin IA, solo convertir y salir ---
if ($NoLlm) {
    Write-Host "==> Conversión PDF->HTML + segmentación (sin IA)..." -ForegroundColor Cyan
    & $venvPy -m rca.cli run-all --no-llm
    return
}

# --- 3) Ollama: verificar instalación y modelo ---
if (-not (Tiene "ollama")) {
    Write-Host "`n[!] Ollama no está instalado." -ForegroundColor Yellow
    Write-Host "    Instálalo:  winget install Ollama.Ollama   (o https://ollama.com/download)"
    Write-Host "    Mientras tanto, corro solo la conversión:" -ForegroundColor Yellow
    & $venvPy -m rca.cli run-all --no-llm
    return
}

$env:RCA_MODELO = $Modelo
$lista = (& ollama list) -join "`n"
$base = $Modelo.Split(":")[0]
if ($lista -notmatch [regex]::Escape($base)) {
    Write-Host "==> Descargando modelo $Modelo (puede tardar)..." -ForegroundColor Cyan
    & ollama pull $Modelo
}

Write-Host "==> Verificando Ollama..." -ForegroundColor Cyan
& $venvPy -m rca.cli check-ollama

# --- 4) Pipeline completo ---
Write-Host "==> Ejecutando pipeline completo..." -ForegroundColor Cyan
& $venvPy -m rca.cli run-all

# --- 5) Abrir resultados ---
$out = Join-Path $raiz "output"
Write-Host "`nListo. Resultados en: $out" -ForegroundColor Green
if (Test-Path (Join-Path $out "matriz_exigencias.xlsx")) {
    Invoke-Item $out
}
