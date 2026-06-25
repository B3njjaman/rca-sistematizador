"""Etapa 0: PDF -> HTML (entregable auditable) + sidecar de texto por página."""
from __future__ import annotations

import html as html_lib
import json
from pathlib import Path

import fitz  # PyMuPDF


_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 2rem auto; line-height: 1.5; color:#222; }}
  .pagina {{ border-bottom: 1px dashed #bbb; padding: 1.5rem 0; }}
  .pagina-num {{ color:#888; font-size:.8rem; font-family: system-ui, sans-serif; }}
  pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: inherit; margin:0; }}
</style>
</head>
<body>
<h1>{titulo}</h1>
{cuerpo}
</body>
</html>
"""


def pdf_a_html(pdf_path: Path, html_dir: Path) -> tuple[Path, Path]:
    """Convierte el PDF a un HTML legible y a un .pages.json (texto por página).

    Devuelve (ruta_html, ruta_pages_json).
    """
    pdf_path = Path(pdf_path)
    html_dir = Path(html_dir)
    html_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    paginas: list[dict] = []
    bloques_html: list[str] = []

    for i, page in enumerate(doc, start=1):
        texto = page.get_text("text")
        paginas.append({"pagina": i, "texto": texto})
        bloques_html.append(
            f'<section class="pagina" data-pagina="{i}">'
            f'<div class="pagina-num">— página {i} —</div>'
            f"<pre>{html_lib.escape(texto)}</pre></section>"
        )
    doc.close()

    titulo = pdf_path.stem
    html = _PLANTILLA.format(titulo=html_lib.escape(titulo), cuerpo="\n".join(bloques_html))

    ruta_html = html_dir / f"{pdf_path.stem}.html"
    ruta_pages = html_dir / f"{pdf_path.stem}.pages.json"
    ruta_html.write_text(html, encoding="utf-8")
    ruta_pages.write_text(json.dumps(paginas, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta_html, ruta_pages
