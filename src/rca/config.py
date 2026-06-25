"""Carga de configuración (settings, taxonomía, mapeo organizacional)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    raiz: Path
    settings: dict
    taxonomia: dict
    mapeo: dict

    # --- accesos cómodos ---
    @property
    def documento(self) -> dict:
        return self.settings.get("documento", {})

    @property
    def ollama(self) -> dict:
        o = dict(self.settings.get("ollama", {}))
        # variables de entorno pueden sobrescribir host/modelo
        o["host"] = os.getenv("OLLAMA_HOST", o.get("host", "http://localhost:11434"))
        o["modelo"] = os.getenv("RCA_MODELO", o.get("modelo", "qwen2.5:3b-instruct"))
        return o

    @property
    def ingesta(self) -> dict:
        return self.settings.get("ingesta", {})

    @property
    def parsing(self) -> dict:
        return self.settings.get("parsing", {})

    def ruta(self, clave: str) -> Path:
        p = self.settings.get("paths", {}).get(clave, clave)
        ruta = (self.raiz / p)
        return ruta

    def asegurar_dirs(self) -> None:
        for clave in ("raw", "html", "output", "cache"):
            self.ruta(clave).mkdir(parents=True, exist_ok=True)


def _leer_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def cargar_config(raiz: Path | str | None = None) -> Config:
    """Carga la configuración desde <raiz>/config/*.yaml."""
    raiz = Path(raiz) if raiz else Path.cwd()
    cfg_dir = raiz / "config"
    return Config(
        raiz=raiz,
        settings=_leer_yaml(cfg_dir / "settings.yaml"),
        taxonomia=_leer_yaml(cfg_dir / "taxonomia.yaml"),
        mapeo=_leer_yaml(cfg_dir / "mapeo_organizacional.yaml"),
    )
