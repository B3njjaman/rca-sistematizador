# =====================================================================
#  Clone + Run. Hace TODO de una:
#    venv -> instalar -> bajar el modelo desde GitHub Release -> importarlo
#    a Ollama -> correr el pipeline -> abrir resultados.
#
#  Uso (desde la carpeta del repo, tras clonar/descomprimir):
#     powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#  Opciones:
#     -NoLlm                  # solo PDF->HTML + segmentación (sin IA)
#     -ModelName "otro"       # nombre del modelo en Ollama
#     -ModelUrl  "<url>"      # otro .gguf (p. ej. el 3B que publiques en Releases)
# =====================================================================
param(
    [switch]$NoLlm,
    [string]$ModelName = "rca-qwen",
    [string]$ModelUrl  = "https://github.com/B3njjaman/rca-sistematizador/releases/download/modelos-v1/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
)
$ErrorActionPreference = "Stop"
$raiz   = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $raiz ".venv\Scripts\python.exe"
$gguf   = Join-Path $raiz "model.gguf"
function Tiene($c) { return [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# --- 1) Entorno virtual + instalación ---
if (-not (Test-Path $venvPy)) {
    Write-Host "==> Creando entorno virtual (.venv)..." -ForegroundColor Cyan
    if (Tiene "python") { python -m venv "$raiz\.venv" }
    elseif (Tiene "py") { py -3 -m venv "$raiz\.venv" }
    else { throw "No se encontró Python 3.10+. Instálalo (winget install Python.Python.3.11) y reabre PowerShell." }
}
Write-Host "==> Instalando dependencias..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -e $raiz

# --- 2) Modo sin IA: convertir y salir ---
if ($NoLlm) {
    & $venvPy -m rca.cli run-all --no-llm
    return
}

# --- 3) Ollama instalado? ---
if (-not (Tiene "ollama")) {
    Write-Host "`n[!] Ollama no está instalado: winget install Ollama.Ollama" -ForegroundColor Yellow
    Write-Host "    Corro solo la conversión por ahora..." -ForegroundColor Yellow
    & $venvPy -m rca.cli run-all --no-llm
    return
}

# --- 4) Asegurar el modelo (SIN usar el registro de Ollama) ---
$yaEsta = (& ollama list 2>$null) -match [regex]::Escape($ModelName)
if (-not $yaEsta) {
    if (-not (Test-Path $gguf) -or (Get-Item $gguf).Length -lt 900MB) {
        Write-Host "==> Descargando modelo desde GitHub Release (red permitida)..." -ForegroundColor Cyan
        if (Test-Path $gguf) { curl.exe -L -C - -o "$gguf" "$ModelUrl" }  # reanuda parcial
        else                 { curl.exe -L -o "$gguf" "$ModelUrl" }       # descarga nueva
    }
    if (-not (Test-Path $gguf) -or (Get-Item $gguf).Length -lt 900MB) {
        throw "La descarga del modelo quedó incompleta. Borra '$gguf' y vuelve a correr el script."
    }
    # validar cabecera GGUF (primeros 4 bytes), sin cargar el archivo entero
    $fs = [System.IO.File]::OpenRead($gguf); $b = New-Object byte[] 4
    $null = $fs.Read($b, 0, 4); $fs.Close()
    if ((-join ($b | ForEach-Object { [char]$_ })) -ne "GGUF") {
        throw "model.gguf no es un GGUF válido (descarga corrupta). Borra el archivo y reintenta."
    }
    Write-Host "==> Importando el modelo a Ollama como '$ModelName' (local, sin internet)..." -ForegroundColor Cyan
    Push-Location $raiz
    try { & ollama create $ModelName -f (Join-Path $raiz "Modelfile") } finally { Pop-Location }
}

# --- 5) Correr el pipeline ---
$env:RCA_MODELO = $ModelName
Write-Host "==> Verificando Ollama..." -ForegroundColor Cyan
& $venvPy -m rca.cli check-ollama
Write-Host "==> Ejecutando pipeline completo..." -ForegroundColor Cyan
& $venvPy -m rca.cli run-all

# --- 6) Abrir resultados ---
$out = Join-Path $raiz "output"
Write-Host "`nListo. Resultados en: $out" -ForegroundColor Green
if (Test-Path (Join-Path $out "matriz_exigencias.xlsx")) { Invoke-Item $out }
