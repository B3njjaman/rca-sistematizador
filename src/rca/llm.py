"""Cliente Ollama con salida estructurada (JSON Schema), caché y reintentos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ollama


def _contenido(resp) -> str:
    """Extrae el texto de la respuesta, tolerando dict o objeto pydantic."""
    try:
        return resp["message"]["content"]
    except (TypeError, KeyError):
        return resp.message.content


class OllamaClient:
    def __init__(
        self,
        host: str,
        modelo: str,
        temperatura: float = 0,
        seed: int = 42,
        num_ctx: int = 4096,
        cache_dir: str | Path = ".cache",
        timeout: int = 600,
    ):
        # timeout amplio: en CPU la primera inferencia (carga + generación con
        # esquema JSON) puede tardar minutos. Sin esto -> "max retries exceeded".
        self.client = ollama.Client(host=host, timeout=timeout)
        self.modelo = modelo
        self.opciones = {"temperature": temperatura, "seed": seed, "num_ctx": num_ctx}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def disponible(self) -> tuple[bool, str]:
        """Verifica conexión y si el modelo está descargado."""
        try:
            data = self.client.list()
            modelos = [m.get("model", m.get("name", "")) for m in data.get("models", [])]
            base = self.modelo.split(":")[0]
            tiene = any(self.modelo == m or m.startswith(base) for m in modelos)
            if not tiene:
                return False, f"Ollama responde, pero el modelo '{self.modelo}' no está. Ejecuta: ollama pull {self.modelo}"
            return True, "ok"
        except Exception as e:  # noqa: BLE001
            return False, f"No se pudo conectar a Ollama ({self.client._client.base_url}): {e}"

    def _clave_cache(self, system: str, user: str, schema: dict) -> Path:
        crudo = json.dumps([self.modelo, system, user, schema, self.opciones],
                           ensure_ascii=False, sort_keys=True)
        h = hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:32]
        return self.cache_dir / f"{h}.json"

    def chat_json(self, system: str, user: str, schema: dict, reintentos: int = 2) -> dict:
        """Llama al modelo forzando salida JSON válida contra `schema`. Cachea por hash."""
        cache = self._clave_cache(system, user, schema)
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))

        ultimo_error: Exception | None = None
        for _ in range(reintentos + 1):
            try:
                resp = self.client.chat(
                    model=self.modelo,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    format=schema,
                    options=self.opciones,
                )
                data = json.loads(_contenido(resp))
                cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                return data
            except Exception as e:  # noqa: BLE001
                ultimo_error = e
        raise RuntimeError(f"Fallo al obtener JSON del modelo tras {reintentos + 1} intentos: {ultimo_error}")
