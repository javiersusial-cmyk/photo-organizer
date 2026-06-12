"""
Detecta estructura ya organizada en las carpetas origen y extrae hints:
año, categoría, ciudad.

Ejemplos que reconoce:
  2019_Viaje_Roma        → year=2019, category=Viajes, city=Roma
  Boda_Maria_2021        → year=2021, category=Eventos
  Navidad_2020           → year=2020, category=Eventos
  Vacaciones_Paris_2018  → year=2018, category=Viajes, city=Paris
  2023                   → year=2023
  fotos_mezcladas        → sin hints
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.geocoder import city_from_folder_name

# Palabras clave en nombres de carpeta → categoría
CATEGORY_KEYWORDS: dict[str, str] = {
    # Viajes
    "viaje":      "Viajes",
    "viajes":     "Viajes",
    "vacacion":   "Viajes",
    "vacaciones": "Viajes",
    "trip":       "Viajes",
    "travel":     "Viajes",
    "tour":       "Viajes",
    "excursion":  "Viajes",
    # Eventos
    "boda":       "Eventos",
    "wedding":    "Eventos",
    "cumple":     "Eventos",
    "cumpleaños": "Eventos",
    "birthday":   "Eventos",
    "navidad":    "Eventos",
    "christmas":  "Eventos",
    "fiesta":     "Eventos",
    "party":      "Eventos",
    "graduacion": "Eventos",
    "comunion":   "Eventos",
    "bautizo":    "Eventos",
    "concierto":  "Eventos",
    "concert":    "Eventos",
    # Familia / Personas
    "familia":    "Familia",
    "family":     "Familia",
    "retrato":    "Personas",
    "portrait":   "Personas",
    # Naturaleza
    "naturaleza": "Naturaleza",
    "nature":     "Naturaleza",
    "paisaje":    "Naturaleza",
    "playa":      "Naturaleza",
    "beach":      "Naturaleza",
    "montana":    "Naturaleza",
    "mountain":   "Naturaleza",
}

_YEAR_RE = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")


@dataclass
class FolderHints:
    year: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None


def extract_folder_hints(path: Path, source_root: Path) -> FolderHints:
    """
    Analiza todas las carpetas en la ruta relativa al origen y devuelve
    los hints encontrados (el más específico gana).
    """
    hints = FolderHints()

    try:
        rel = path.relative_to(source_root)
        parts = rel.parts[:-1]  # excluir el nombre del fichero
    except ValueError:
        return hints

    for part in parts:
        lower = part.lower()
        normalized = re.sub(r"[_\-\s]+", " ", lower)

        # Año
        m = _YEAR_RE.search(part)
        if m and hints.year is None:
            hints.year = m.group(1)

        # Ciudad (tiene prioridad sobre categoría para Viajes)
        city = city_from_folder_name(normalized)
        if city and hints.city is None:
            hints.city = city
            hints.category = "Viajes"

        # Categoría por palabra clave
        if hints.category is None:
            for keyword, category in CATEGORY_KEYWORDS.items():
                if keyword in normalized:
                    hints.category = category
                    break

    return hints
