"""Etapa 3: clasificación de cada exigencia con taxonomía controlada (LLM local)."""
from __future__ import annotations

from pathlib import Path

from .llm import OllamaClient
from .schema import RIESGOS, Clasificacion, Exigencia

_PROMPT_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _system_prompt(taxonomia: dict) -> str:
    plantilla = (_PROMPT_DIR / "clasificar.txt").read_text(encoding="utf-8") \
        if (_PROMPT_DIR / "clasificar.txt").exists() else _DEFECTO
    return plantilla.format(
        componentes=", ".join(taxonomia.get("componentes", [])),
        elementos=", ".join(taxonomia.get("elementos", [])),
        areas=", ".join(taxonomia.get("areas", [])),
    )


_DEFECTO = (
    "Clasifica la exigencia ambiental. Componentes posibles: {componentes}. "
    "Elementos posibles: {elementos}. Áreas/obras posibles: {areas}. "
    "Riesgo inherente: Alto, Medio, Bajo o No determinado. Devuelve JSON."
)


def _sanea(valor, permitidos: list[str], defecto: str) -> str:
    return valor if valor in permitidos else defecto


def clasificar(exigencias: list[Exigencia], client: OllamaClient, taxonomia: dict) -> list[Exigencia]:
    system = _system_prompt(taxonomia)
    schema = Clasificacion.model_json_schema()

    for ex in exigencias:
        entrada = f"NOMBRE: {ex.nombre}\nTEXTO: {ex.transcripcion_literal}"
        try:
            data = client.chat_json(system, entrada, schema)
            data["riesgo_inherente"] = _sanea(data.get("riesgo_inherente"), RIESGOS, "No determinado")
            c = Clasificacion.model_validate(data)
        except Exception:  # noqa: BLE001
            continue
        ex.componente_1 = c.componente_1 or ex.componente_1
        ex.componente_2 = c.componente_2
        ex.elemento_2 = c.elemento_2
        ex.componente_3 = c.componente_3
        ex.elemento_3 = c.elemento_3
        ex.area_1 = c.area_1
        ex.obra_actividad_1 = c.obra_actividad_1
        ex.area_2 = c.area_2
        ex.obra_actividad_2 = c.obra_actividad_2
        ex.area_3 = c.area_3
        ex.obra_actividad_3 = c.obra_actividad_3
        ex.riesgo_inherente = c.riesgo_inherente
    return exigencias
