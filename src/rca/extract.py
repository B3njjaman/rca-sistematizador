"""Etapa 2: extracción de exigencias por bloque, con el LLM local."""
from __future__ import annotations

from pathlib import Path

from .llm import OllamaClient
from .parse import Chunk
from .schema import (
    FASES,
    FRECUENCIAS,
    TIPOS,
    Exigencia,
    ExigenciaExtraida,
    ResultadoExtraccion,
)
from .verify import verificar

_PROMPT_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _system_prompt() -> str:
    f = _PROMPT_DIR / "extraer_exigencias.txt"
    if f.exists():
        return f.read_text(encoding="utf-8")
    return (
        "Eres un analista ambiental experto en RCA chilenas. Extrae las exigencias "
        "(obligaciones, condiciones, compromisos, medidas, planes) del texto. "
        "La transcripción debe ser EXACTA, copiada del texto. Devuelve JSON."
    )


def _sanea(valor, permitidos: list[str], defecto: str) -> str:
    return valor if valor in permitidos else defecto


def extraer(chunks: list[Chunk], client: OllamaClient) -> list[Exigencia]:
    system = _system_prompt()
    schema = ResultadoExtraccion.model_json_schema()
    salida: list[Exigencia] = []

    for ch in chunks:
        data = client.chat_json(system, ch.texto, schema)
        for item in data.get("exigencias", []):
            # saneo tolerante de los campos de vocabulario cerrado
            item["tipo"] = _sanea(item.get("tipo"), TIPOS, "Otro")
            item["fase"] = _sanea(item.get("fase"), FASES, "No determinado")
            item["frecuencia"] = _sanea(item.get("frecuencia"), FRECUENCIAS, "No determinada")
            try:
                e = ExigenciaExtraida.model_validate(item)
            except Exception:  # noqa: BLE001
                continue
            ex = Exigencia(
                fuente=ch.fuente,
                pagina=str(ch.pagina),
                nombre=e.nombre,
                transcripcion_literal=e.transcripcion_literal,
                tipo=e.tipo,
                fase=e.fase,
                frecuencia=e.frecuencia,
                restriccion_ambiental=e.restriccion_ambiental,
                verificadores_propuestos=e.verificadores_propuestos,
                antecedentes_complementarios=e.antecedentes_complementarios,
            )
            verificar(ex, ch.texto)
            salida.append(ex)
    return salida
