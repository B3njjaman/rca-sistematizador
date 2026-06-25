"""Verificación anti-alucinación: la transcripción literal debe existir en la fuente."""
from __future__ import annotations

import re

from .schema import Exigencia


def _norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def verificar(ex: Exigencia, texto_fuente: str, min_frag: int = 40) -> None:
    """Marca la exigencia como verificada si su transcripción aparece en la fuente."""
    objetivo = _norm(ex.transcripcion_literal)
    fuente = _norm(texto_fuente)
    if not objetivo:
        ex.verificada = False
        ex.requiere_revision = True
        ex.nota_revision = "Sin transcripción literal"
        return

    fragmento = objetivo[: max(min_frag, min(120, len(objetivo)))]
    if fragmento in fuente:
        ex.verificada = True
        ex.requiere_revision = False
        ex.nota_revision = ""
    else:
        ex.verificada = False
        ex.requiere_revision = True
        ex.nota_revision = "La transcripción no calza literalmente con la fuente: revisar"
