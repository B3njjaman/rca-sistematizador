"""CLI del sistematizador de RCA.

Comandos:
  rca check-ollama          -> verifica conexión y modelo
  rca convert [PDF]         -> PDF a HTML (+ pages.json)   [no requiere LLM]
  rca run-all [PDF]         -> pipeline completo -> matriz Excel/CSV/JSON/HTML
        opciones: --no-llm (solo convertir+segmentar), --no-classify
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import classify as _classify
from . import enrich as _enrich
from . import export as _export
from . import extract as _extract
from .config import cargar_config
from .ingest import pdf_a_html
from .llm import OllamaClient
from .parse import cargar_chunks

app = typer.Typer(add_completion=False, help="Sistematiza una RCA con modelos locales (Ollama).")
console = Console()


def _cfg():
    cfg = cargar_config(Path.cwd())
    cfg.asegurar_dirs()
    return cfg


def _resolver_pdf(cfg, pdf: str | None) -> Path:
    if pdf:
        return Path(pdf)
    candidatos = sorted(cfg.ruta("raw").glob("*.pdf")) + sorted(cfg.ruta("raw").glob("*.PDF"))
    if not candidatos:
        console.print(f"[red]No hay PDFs en {cfg.ruta('raw')}. Pasa la ruta: rca run-all <pdf>[/red]")
        raise typer.Exit(1)
    return candidatos[0]


def _cliente(cfg) -> OllamaClient:
    o = cfg.ollama
    return OllamaClient(
        host=o["host"], modelo=o["modelo"], temperatura=o.get("temperatura", 0),
        seed=o.get("seed", 42), num_ctx=o.get("num_ctx", 4096), cache_dir=str(cfg.ruta("cache")),
        timeout=o.get("timeout", 600),
    )


@app.command("check-ollama")
def check_ollama():
    """Verifica que Ollama esté arriba y el modelo descargado."""
    cfg = _cfg()
    ok, msg = _cliente(cfg).disponible()
    if ok:
        console.print(f"[green]✓ Ollama OK[/green] — modelo: {cfg.ollama['modelo']}")
    else:
        console.print(f"[red]✗ {msg}[/red]")
        raise typer.Exit(1)


@app.command()
def convert(pdf: str = typer.Argument(None, help="Ruta al PDF (por defecto, el primero en data/raw).")):
    """Convierte el PDF a HTML (entregable) y deja el sidecar de texto por página."""
    cfg = _cfg()
    ruta_pdf = _resolver_pdf(cfg, pdf)
    console.print(f"Convirtiendo [cyan]{ruta_pdf.name}[/cyan] -> HTML…")
    ruta_html, ruta_pages = pdf_a_html(ruta_pdf, cfg.ruta("html"))
    console.print(f"[green]✓[/green] HTML: {ruta_html}")
    console.print(f"[green]✓[/green] Texto por página: {ruta_pages}")


@app.command("run-all")
def run_all(
    pdf: str = typer.Argument(None, help="Ruta al PDF (por defecto, el primero en data/raw)."),
    no_llm: bool = typer.Option(False, "--no-llm", help="Solo convertir y segmentar (sin extracción LLM)."),
    no_classify: bool = typer.Option(False, "--no-classify", help="Omitir la clasificación con taxonomía."),
):
    """Pipeline completo: PDF -> HTML -> exigencias -> matriz."""
    cfg = _cfg()
    ruta_pdf = _resolver_pdf(cfg, pdf)

    # [0] Convertir
    console.print(f"[bold][0][/bold] Convirtiendo {ruta_pdf.name} -> HTML…")
    ruta_html, ruta_pages = pdf_a_html(ruta_pdf, cfg.ruta("html"))
    console.print(f"    HTML: {ruta_html}")

    # [1] Segmentar
    console.print("[bold][1][/bold] Segmentando en bloques con 'Fuente'…")
    chunks = cargar_chunks(ruta_pages, max_chars=cfg.parsing.get("max_chars_chunk", 4000))
    console.print(f"    {len(chunks)} bloques")

    if no_llm:
        console.print("[yellow]--no-llm: me detengo tras segmentar. Revisa el HTML y los bloques.[/yellow]")
        return

    # comprobar Ollama antes de gastar tiempo
    cliente = _cliente(cfg)
    ok, msg = cliente.disponible()
    if not ok:
        console.print(f"[red]✗ {msg}[/red]")
        console.print("[yellow]Sugerencia: corre 'rca run-all --no-llm' para validar la conversión sin modelo.[/yellow]")
        raise typer.Exit(1)

    # [2] Extraer
    console.print("[bold][2][/bold] Extrayendo exigencias con el LLM local…")
    exigencias = _extract.extraer(chunks, cliente)
    console.print(f"    {len(exigencias)} exigencias")

    # [3] Clasificar
    if not no_classify and exigencias:
        console.print("[bold][3][/bold] Clasificando (componentes/áreas/riesgo)…")
        _classify.clasificar(exigencias, cliente, cfg.taxonomia)

    # [4] Enriquecer (IDs, metadata, operativos)
    console.print("[bold][4][/bold] Asignando IDs, metadata y campos operativos…")
    _enrich.enriquecer(exigencias, cfg.documento, cfg.mapeo)

    # [5] Export
    console.print("[bold][5][/bold] Exportando matriz…")
    res = _export.exportar(exigencias, cfg.ruta("output"))

    _resumen(exigencias, res)


def _resumen(exigencias, res):
    n = len(exigencias)
    rev = sum(1 for e in exigencias if e.requiere_revision)
    t = Table(title="Resultado")
    t.add_column("Métrica"); t.add_column("Valor", justify="right")
    t.add_row("Exigencias", str(n))
    t.add_row("Requieren revisión (literal)", str(rev))
    t.add_row("Excel", str(res["xlsx"]))
    t.add_row("CSV", str(res["csv"]))
    t.add_row("HTML", str(res["html"]))
    console.print(t)
    if rev:
        console.print(f"[yellow]⚠ {rev} fila(s) marcadas 'Revisar' (transcripción no calzó literal).[/yellow]")


if __name__ == "__main__":
    app()
