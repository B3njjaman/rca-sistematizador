"""Modelo de datos: una Exigencia = una fila de la matriz, con tus 31 columnas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# --- Vocabularios cerrados (van como enum en el JSON Schema de Ollama) ---
TipoLit = Literal[
    "Compromiso Ambiental Voluntario",
    "Condición o Exigencia de la RCA",
    "Norma de carácter ambiental",
    "Permiso Ambiental Sectorial (PAS)",
    "Medida de mitigación, reparación o compensación",
    "Plan de Seguimiento de Variables Ambientales",
    "Plan de Cumplimiento",
    "Otro",
]
FaseLit = Literal["Construcción", "Operación", "Cierre", "Transversal", "No determinado"]
FrecuenciaLit = Literal[
    "Única", "Diaria", "Semanal", "Mensual", "Trimestral",
    "Semestral", "Anual", "Permanente", "Según evento", "No determinada",
]
RiesgoLit = Literal["Alto", "Medio", "Bajo", "No determinado"]

# Listas equivalentes para validar/sanear respuestas del LLM.
TIPOS = list(TipoLit.__args__)
FASES = list(FaseLit.__args__)
FRECUENCIAS = list(FrecuenciaLit.__args__)
RIESGOS = list(RiesgoLit.__args__)


# ============================================================
#  Lo que el LLM devuelve en la ETAPA DE EXTRACCIÓN
# ============================================================
class ExigenciaExtraida(BaseModel):
    nombre: str = Field(description="Título breve de la exigencia")
    transcripcion_literal: str = Field(description="Texto EXACTO, copiado de la fuente, sin parafrasear")
    tipo: TipoLit
    fase: FaseLit
    frecuencia: FrecuenciaLit
    restriccion_ambiental: Optional[str] = None
    verificadores_propuestos: Optional[str] = None
    antecedentes_complementarios: Optional[str] = None


class ResultadoExtraccion(BaseModel):
    exigencias: list[ExigenciaExtraida] = Field(default_factory=list)


# ============================================================
#  Lo que el LLM devuelve en la ETAPA DE CLASIFICACIÓN
# ============================================================
class Clasificacion(BaseModel):
    componente_1: str
    componente_2: Optional[str] = None
    elemento_2: Optional[str] = None
    componente_3: Optional[str] = None
    elemento_3: Optional[str] = None
    area_1: Optional[str] = None
    obra_actividad_1: Optional[str] = None
    area_2: Optional[str] = None
    obra_actividad_2: Optional[str] = None
    area_3: Optional[str] = None
    obra_actividad_3: Optional[str] = None
    riesgo_inherente: RiesgoLit


# ============================================================
#  Registro canónico (acumula todas las etapas -> fila final)
# ============================================================
class Exigencia(BaseModel):
    # provenance / metadata
    id_exigencia: str = ""
    compania: str = ""
    proyecto: str = ""
    instrumento: str = ""
    fuente: str = ""
    pagina: str = ""

    # extraídas (del texto)
    nombre: str = ""
    transcripcion_literal: str = ""
    tipo: str = ""
    fase: str = ""
    frecuencia: str = ""
    restriccion_ambiental: Optional[str] = None
    verificadores_propuestos: Optional[str] = None
    antecedentes_complementarios: Optional[str] = None

    # clasificadas (taxonomía)
    componente_1: str = ""
    componente_2: Optional[str] = None
    elemento_2: Optional[str] = None
    componente_3: Optional[str] = None
    elemento_3: Optional[str] = None
    area_1: Optional[str] = None
    obra_actividad_1: Optional[str] = None
    area_2: Optional[str] = None
    obra_actividad_2: Optional[str] = None
    area_3: Optional[str] = None
    obra_actividad_3: Optional[str] = None
    riesgo_inherente: str = "No determinado"

    # operativas (las completa el equipo de cumplimiento)
    fecha_inicio: str = ""
    fecha_fin: str = ""
    estado_cumplimiento: str = "No iniciado"
    responsable: str = ""
    gerencia: str = ""
    superintendencia: str = ""

    # auditoría
    verificada: bool = False
    requiere_revision: bool = False
    nota_revision: str = ""

    def to_row(self) -> dict:
        """Mapea a las columnas finales (nombres en español, con tildes)."""
        return {
            "Nombre Exigencia": self.nombre,
            "Compañía": self.compania,
            "ID Exigencia": self.id_exigencia,
            "Transcripción Literal": self.transcripcion_literal,
            "Fuente": self.fuente,
            "Proyecto": self.proyecto,
            "Componente 1": self.componente_1,
            "Componente 2": self.componente_2 or "",
            "Elemento 2": self.elemento_2 or "",
            "Componente 3": self.componente_3 or "",
            "Elemento 3": self.elemento_3 or "",
            "Área 1": self.area_1 or "",
            "Obra instalación o actividad 1": self.obra_actividad_1 or "",
            "Área 2": self.area_2 or "",
            "Obra, instalación o actividad 2": self.obra_actividad_2 or "",
            "Área 3": self.area_3 or "",
            "Obra, instalación o actividad 3": self.obra_actividad_3 or "",
            "Restricción ambiental": self.restriccion_ambiental or "",
            "Antecedentes Complementarios": self.antecedentes_complementarios or "",
            "Fase del proyecto": self.fase,
            "Instrumento o Documento": self.instrumento,
            "Fecha inicio": self.fecha_inicio,
            "Fecha Fin": self.fecha_fin,
            "Riesgo Inherente": self.riesgo_inherente,
            "Tipo de Exigencia": self.tipo,
            "Frecuencia": self.frecuencia,
            "Verificadores Propuestos": self.verificadores_propuestos or "",
            "Estado de cumplimiento": self.estado_cumplimiento,
            "Responsable": self.responsable,
            "Gerencia": self.gerencia,
            "Superintendencia": self.superintendencia,
            # columnas de auditoría (extra, ayudan a la revisión humana)
            "Página": self.pagina,
            "Verificación literal": "OK" if self.verificada else "Revisar",
            "Requiere revisión": "Sí" if self.requiere_revision else "No",
            "Nota revisión": self.nota_revision,
        }


# 31 columnas solicitadas, en el orden pedido (sin la repetición de "Restricción ambiental").
COLUMNAS = [
    "Nombre Exigencia", "Compañía", "ID Exigencia", "Transcripción Literal", "Fuente",
    "Proyecto", "Componente 1", "Componente 2", "Elemento 2", "Componente 3", "Elemento 3",
    "Área 1", "Obra instalación o actividad 1", "Área 2", "Obra, instalación o actividad 2",
    "Área 3", "Obra, instalación o actividad 3", "Restricción ambiental",
    "Antecedentes Complementarios", "Fase del proyecto", "Instrumento o Documento",
    "Fecha inicio", "Fecha Fin", "Riesgo Inherente", "Tipo de Exigencia", "Frecuencia",
    "Verificadores Propuestos", "Estado de cumplimiento", "Responsable", "Gerencia",
    "Superintendencia",
]
# Columnas de auditoría que se agregan al final del export.
COLUMNAS_AUDITORIA = ["Página", "Verificación literal", "Requiere revisión", "Nota revisión"]
COLUMNAS_EXPORT = COLUMNAS + COLUMNAS_AUDITORIA
