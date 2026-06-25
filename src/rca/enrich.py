"""Etapa 4: metadata, IDs y campos operativos (con sugerencias organizacionales)."""
from __future__ import annotations

from .schema import Exigencia


def enriquecer(exigencias: list[Exigencia], documento: dict, mapeo: dict) -> list[Exigencia]:
    prefijo = documento.get("id_prefijo", "EX")
    por_componente = mapeo.get("por_componente", {})
    default = mapeo.get("default", {})

    for i, ex in enumerate(exigencias, start=1):
        ex.id_exigencia = f"{prefijo}-{i:03d}"
        ex.compania = documento.get("compania", "")
        ex.proyecto = documento.get("proyecto", "")
        ex.instrumento = documento.get("instrumento", "")

        # sugerencia de responsable organizacional según componente 1
        sug = por_componente.get(ex.componente_1, default)
        if not ex.gerencia:
            ex.gerencia = sug.get("gerencia", "")
        if not ex.superintendencia:
            ex.superintendencia = sug.get("superintendencia", "")

        if not ex.estado_cumplimiento:
            ex.estado_cumplimiento = "No iniciado"
    return exigencias
