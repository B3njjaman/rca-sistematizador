"""Etapa 1: texto por página -> bloques (chunks) con su 'Fuente'.

Heurística sin LLM. Detecta encabezados típicos de una RCA (CONSIDERANDO,
RESUELVO, ítems numerados, PAS, Compromisos, Plan de Seguimiento) para etiquetar
la procedencia de cada bloque (columna 'Fuente') y mantener trazabilidad.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    texto: str
    fuente: str
    pagina: int


# Marcadores ESTRUCTURALES (rara aparición, autoritativos). Tolerantes a letras
# espaciadas, p. ej. "C O N S I D E R A N D O", típicas de resoluciones del SEA.
# En MAYÚSCULA (sin re.I): así no confundimos con el gerundio "considerando" en
# minúscula dentro del cuerpo. Toleran letras espaciadas y ":" opcional.
_ESTRUCTURAL = [
    (re.compile(r"C\s*O\s*N\s*S\s*I\s*D\s*E\s*R\s*A\s*N\s*D\s*O\s*:?"), "Considerando"),
    (re.compile(r"R\s*E\s*S\s*U\s*E\s*L\s*V[OE]\s*:?"), "Resuelvo"),
    (re.compile(r"\bV\s*I\s*S\s*T\s*O\s*S\s*:?"), "Vistos"),
]
# Marcadores TEMÁTICOS (solo cuentan si aparecen como encabezado, al inicio del párrafo).
_TEMATICO = [
    (re.compile(r"compromisos?\s+ambientales?\s+voluntarios?", re.I), "Compromisos Ambientales Voluntarios"),
    (re.compile(r"permisos?\s+ambientales?\s+sectoriales?|\bPAS\s*N", re.I), "Permisos Ambientales Sectoriales"),
    (re.compile(r"plan\s+de\s+seguimiento", re.I), "Plan de Seguimiento"),
    (re.compile(r"plan\s+de\s+cumplimiento", re.I), "Plan de Cumplimiento"),
    (re.compile(r"condiciones?\s+(o|y)\s+exigencias?", re.I), "Condiciones o Exigencias"),
]
# Ítem numerado al inicio de línea: "9.", "9.2", "12)", "1°." ...
_NUMERADO = re.compile(r"^\s*(\d+(?:\.\d+)*)[°\.\)]\s+")


def _detectar_seccion(parrafo: str, actual: str) -> str:
    # estructural: busca en todo el párrafo y toma el marcador MÁS RECIENTE
    mejor_pos, mejor_et = -1, None
    for patron, etiqueta in _ESTRUCTURAL:
        ultimo = None
        for m in patron.finditer(parrafo):
            ultimo = m
        if ultimo and ultimo.start() > mejor_pos:
            mejor_pos, mejor_et = ultimo.start(), etiqueta
    if mejor_et:
        return mejor_et
    # temático: solo si aparece como encabezado (primeros 80 caracteres)
    cabeza = parrafo[:80]
    for patron, etiqueta in _TEMATICO:
        if patron.search(cabeza):
            return etiqueta
    return actual


def _parrafos(texto: str) -> list[str]:
    # une saltos sueltos, separa por líneas en blanco
    bruto = re.split(r"\n\s*\n", texto)
    return [re.sub(r"[ \t]+", " ", p.strip()) for p in bruto if p.strip()]


def construir_chunks(pages: list[dict], max_chars: int = 4000) -> list[Chunk]:
    chunks: list[Chunk] = []
    seccion = "Encabezado"
    numero = ""
    buffer: list[str] = []
    buf_pagina = pages[0]["pagina"] if pages else 1
    buf_fuente = seccion

    def flush():
        nonlocal buffer
        if buffer:
            chunks.append(Chunk(texto="\n\n".join(buffer).strip(), fuente=buf_fuente, pagina=buf_pagina))
            buffer = []

    for page in pages:
        pagina = page["pagina"]
        for parrafo in _parrafos(page["texto"]):
            nueva_seccion = _detectar_seccion(parrafo, seccion)
            m = _NUMERADO.match(parrafo)
            cambia = (nueva_seccion != seccion) or (m is not None)

            if cambia and buffer:
                flush()
            if nueva_seccion != seccion:
                seccion = nueva_seccion
                numero = ""  # número de ítem no se arrastra entre secciones
            if m:
                numero = m.group(1)

            if not buffer:
                buf_pagina = pagina
                buf_fuente = f"{seccion} N°{numero}".strip() if numero else seccion
                buf_fuente = f"{buf_fuente} (pág. {pagina})"

            buffer.append(parrafo)
            if sum(len(x) for x in buffer) >= max_chars:
                flush()
    flush()
    return chunks


def cargar_chunks(pages_json: Path, max_chars: int = 4000) -> list[Chunk]:
    pages = json.loads(Path(pages_json).read_text(encoding="utf-8"))
    return construir_chunks(pages, max_chars=max_chars)


def chunks_a_dicts(chunks: list[Chunk]) -> list[dict]:
    return [c.__dict__ for c in chunks]
