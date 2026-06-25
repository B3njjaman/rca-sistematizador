# rca-sistematizador

Convierte una **RCA (Resolución de Calificación Ambiental)** en PDF a **HTML** y la
**sistematiza** en una matriz de exigencias (31 columnas), usando **modelos locales con Ollama**.
Pensado para correr 100% offline en CPU.

Primer caso: `RCA N°0058/2019 – Actualización Proyecto Desarrollo Minera Centinela`.

## Pipeline

```
PDF ─►[0] HTML ─►[1] bloques+Fuente ─►[2] extracción LLM ─►[3] clasificación ─►[4] operativos ─►[5] Excel/CSV/JSON/HTML
```

- **[0] Ingesta:** `PyMuPDF` convierte el PDF a HTML legible (`data/html/*.html`) y a un sidecar de texto por página.
- **[1] Parsing:** heurística sin LLM que segmenta el documento y etiqueta la *Fuente* (Considerando, PAS, Plan de Seguimiento, página).
- **[2] Extracción:** Ollama con **salida JSON forzada por esquema** (Pydantic). La *Transcripción Literal* se **verifica contra el texto fuente** (anti-alucinación).
- **[3] Clasificación:** componentes/elementos/áreas/riesgo con **taxonomía controlada** (`config/taxonomia.yaml`).
- **[4] Operativos:** IDs, metadata y sugerencia de Gerencia/Superintendencia. Estado por defecto `No iniciado`.
- **[5] Export:** `output/matriz_exigencias.{xlsx,csv,json,html}`.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/download) (para las etapas 2 y 3)

## Instalación rápida (Windows / PowerShell)

Un solo comando hace todo: crea `.venv`, instala, verifica Ollama, descarga el modelo y corre el pipeline.

```powershell
# desde la raíz del repo (tras clonar)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Opciones:

```powershell
.\scripts\setup.ps1 -NoLlm                      # solo PDF->HTML + segmentación (sin IA)
.\scripts\setup.ps1 -Modelo "qwen2.5:7b-instruct"   # PC con 16GB+
```

Si Ollama aún no está instalado, el script avisa y corre solo la conversión.

### Manual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Uso

```powershell
# 0) Coloca el PDF de la RCA en data/raw/  (ya incluido el de Centinela)

# 1) Solo conversión + segmentación (no requiere modelo):
python -m rca.cli run-all --no-llm

# 2) Instala el modelo local (una vez):
ollama pull qwen2.5:3b-instruct
python -m rca.cli check-ollama

# 3) Pipeline completo -> matriz:
python -m rca.cli run-all
```

Salidas en `output/`: `matriz_exigencias.xlsx` (principal), `.csv`, `.json` y `.html`.

## Las 31 columnas

| Origen | Columnas |
|---|---|
| **Metadata** (config) | Compañía, Proyecto, Instrumento o Documento |
| **Provenance** (parser) | ID Exigencia, Fuente, Página |
| **Extraídas** (LLM, del texto) | Nombre Exigencia, Transcripción Literal, Tipo de Exigencia, Frecuencia, Fase del proyecto, Restricción ambiental, Verificadores Propuestos, Antecedentes Complementarios |
| **Clasificadas** (LLM + taxonomía) | Componente 1/2/3, Elemento 2/3, Área 1/2/3, Obra/instalación/actividad 1/2/3, Riesgo Inherente |
| **Operativas** (las llena el equipo) | Fecha inicio, Fecha Fin, Estado de cumplimiento, Responsable, Gerencia, Superintendencia |

> La columna *Restricción ambiental* aparecía dos veces en el requerimiento; se consolidó en una.

## Configuración

- `config/settings.yaml` — modelo Ollama, metadata del documento, rutas, tamaño de bloque.
- `config/taxonomia.yaml` — vocabularios de Componentes/Elementos/Áreas.
- `config/mapeo_organizacional.yaml` — sugerencias Componente → Gerencia/Superintendencia.

Cambiar de modelo (ej. con 16 GB): edita `ollama.modelo` a `qwen2.5:7b-instruct`, o exporta `RCA_MODELO`.

## Estructura

```
src/rca/    ingest · parse · llm · extract · classify · enrich · verify · export · cli
config/     settings · taxonomia · mapeo_organizacional
prompts/    extraer_exigencias · clasificar
data/raw/   PDFs (no versionados)   data/html/  HTML convertido
output/     matrices generadas
tests/      pytest
```

## Decisiones de diseño

- **Auditabilidad:** cada fila guarda *Fuente* + *Página* y un flag de verificación literal.
- **Reproducibilidad:** `temperature=0`, `seed` fijo y **caché por hash** → re-correr da el mismo resultado.
- **Modular para modelos chicos:** extracción y clasificación son llamadas separadas y simples (mejor recall en 3B).

## Roadmap

- Fase 2: OCR fallback (PDF escaneados) y validación cruzada de la transcripción.
- Fase 3: UI de revisión (Streamlit) y soporte multi-RCA (DuckDB).
