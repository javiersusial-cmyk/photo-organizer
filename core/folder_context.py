"""
Analiza el nombre de una carpeta origen y decide:
  - Si tiene SENTIDO (viaje, ciudad, evento...) → Camino A: conservar nombre
  - Si es un volcado sin contexto (cámara, fechas sueltas) → Camino B: IA

Extrae de las carpetas con sentido: tipo, nombre limpio y fecha (si la trae).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Palabras de carpeta padre/propia → Tipo de salida
TYPE_KEYWORDS: dict[str, str] = {
    "viaje":         "Viaje",
    "viajes":        "Viaje",
    "vacaciones":    "Viaje",
    "ciudad":        "Ciudad",
    "ciudades":      "Ciudad",
    "lugar":         "Ciudad",
    "lugares":       "Ciudad",
    "excursion":     "Excursión",
    "excursiones":   "Excursión",
    "celebracion":   "Evento",
    "celebraciones": "Evento",
    "boda":          "Evento",
    "bodas":         "Evento",
    "cumpleaños":    "Evento",
    "cumpleanos":    "Evento",
    "cumple":        "Evento",
    "bautizo":       "Evento",
    "comunion":      "Evento",
    "evento":        "Evento",
    "eventos":       "Evento",
    "fiesta":        "Evento",
    "nochevieja":    "Evento",
    "navidad":       "Evento",
    "deportiva":     "Evento deportivo",
    "deportivas":    "Evento deportivo",
    "deporte":       "Evento deportivo",
    "partido":       "Evento deportivo",
    "maraton":       "Evento deportivo",
    "family":        "Personas",
    "familia":       "Personas",
    "amigos":        "Personas",
    "personas":      "Personas",
    "cuadrilla":     "Personas",
    "naturaleza":    "Naturaleza",
}

# Carpetas que indican volcado SIN contexto → forzar Camino B (IA)
DUMP_KEYWORDS = {
    "camara", "camaras", "camera", "dcim", "tarjeta", "fotos olympus",
    "fotos pentax", "fotos sony", "fotos galaxy", "100pentx", "100olymp",
    "112_pana", "k10d", "dropbox", "subir web", "sin titulo", "miscelanea",
    "varios", "fotos", "foto", "photos",
}

_YEAR_RE  = re.compile(r"\b(19\d{2}|20[0-3]\d)\b")
_DATE8_RE = re.compile(r"\b(19\d{2}|20[0-3]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b")
_DATE6_RE = re.compile(r"\b(19\d{2}|20[0-3]\d)(0[1-9]|1[0-2])\b")
_MESES = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,
    "agosto":8,"septiembre":9,"setiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
}


def _norm(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@dataclass
class FolderContext:
    meaningful: bool                 # True → Camino A; False → Camino B (IA)
    tipo: Optional[str] = None       # Viaje, Ciudad, Evento, ...
    nombre: Optional[str] = None     # nombre limpio del evento/lugar
    explicit_date: Optional[str] = None  # fecha del nombre, ya formateada
    explicit_year: Optional[str] = None  # año del nombre si lo trae


def _detect_type(parts_norm: list[str]) -> Optional[str]:
    """Busca el tipo en las carpetas de la ruta (de más profunda a más externa)."""
    for part in reversed(parts_norm):
        for word in re.split(r"[^a-z0-9ñ]+", part):
            if word in TYPE_KEYWORDS:
                return TYPE_KEYWORDS[word]
    return None


def _is_dump(parts_norm: list[str]) -> bool:
    """Volcado si la hoja O cualquier carpeta ancestro es de cámara/genérica."""
    leaf_norm = parts_norm[-1] if parts_norm else ""
    # Cualquier ancestro que sea carpeta de cámara/volcado
    for part in parts_norm:
        for kw in ("camara", "camaras", "camera", "dcim", "dropbox"):
            if kw in part:
                return True
    for kw in DUMP_KEYWORDS:
        if kw in leaf_norm:
            return True
    # Carpeta tipo fecha pura "2003-04-12" o "1980-01-06 #2"
    if re.match(r"^\d{4}-\d{2}-\d{2}", leaf_norm.strip()):
        return True
    return False


def _clean_name(leaf: str, tipo: Optional[str]) -> str:
    """Quita fechas y palabras de tipo del nombre de carpeta."""
    name = leaf
    # Quitar fecha de 8 y 6 dígitos
    name = _DATE8_RE.sub(" ", name)
    name = _DATE6_RE.sub(" ", name)
    # Quitar año y mes textual
    name = _YEAR_RE.sub(" ", name)
    for mes in _MESES:
        name = re.sub(rf"\b{mes}\b", " ", name, flags=re.IGNORECASE)
    # Quitar palabras de tipo
    for word in list(TYPE_KEYWORDS.keys()):
        name = re.sub(rf"\b{word}\b", " ", name, flags=re.IGNORECASE)
    # Quitar prefijo "X " (marcador del usuario) y paréntesis vacíos
    name = re.sub(r"\(\s*\)", " ", name)
    name = re.sub(r"^\s*[xX]\s+", " ", name)
    name = re.sub(r"[-_\s]+", " ", name).strip(" -_")
    return name or leaf.strip()


def _extract_date(leaf: str) -> tuple[Optional[str], Optional[str]]:
    """Devuelve (etiqueta_fecha, año) extraídos del nombre, o (None, None)."""
    m8 = _DATE8_RE.search(leaf)
    if m8:
        y, mo, d = m8.group(1), m8.group(2), m8.group(3)
        return f"{y}{mo}{d}", y
    m6 = _DATE6_RE.search(leaf)
    if m6:
        y, mo = m6.group(1), m6.group(2)
        return f"{y}{mo}", y
    # Año + mes textual
    my = _YEAR_RE.search(leaf)
    if my:
        year = my.group(1)
        leaf_norm = _norm(leaf)
        for mes, num in _MESES.items():
            if mes in leaf_norm:
                return f"{year} {mes.capitalize()}", year
        return year, year
    return None, None


def analyze_folder(folder: Path, source_root: Path) -> FolderContext:
    """Analiza la carpeta hoja que contiene las fotos."""
    try:
        rel = folder.relative_to(source_root)
        parts = list(rel.parts)
    except ValueError:
        parts = [folder.name]

    if not parts:
        return FolderContext(meaningful=False)

    # Subcarpetas genéricas que heredan el contexto del padre
    GENERIC_SUB = {"cambiadas", "originales", "editadas", "seleccion", "copia",
                   "copias", "tarjeta 1", "tarjeta 2", "tarjeta", "raw", "jpg"}
    # Si la hoja es genérica y hay padre con nombre, usar el padre como hoja efectiva
    while len(parts) >= 2 and _norm(parts[-1]) in GENERIC_SUB:
        parts = parts[:-1]

    leaf       = parts[-1]
    leaf_norm  = _norm(leaf)
    parts_norm = [_norm(p) for p in parts]

    tipo    = _detect_type(parts_norm)
    is_dump = _is_dump(parts_norm)

    # Volcado de cámara/genérico sin tipo → Camino B (IA)
    if is_dump and tipo is None:
        return FolderContext(meaningful=False)

    date_label, year = _extract_date(leaf)
    nombre = _clean_name(leaf, tipo)

    # Sin tipo pero con nombre propio (no volcado) → tipo genérico "Varios"
    if tipo is None:
        tipo = "Varios"

    return FolderContext(
        meaningful    = True,
        tipo          = tipo,
        nombre        = nombre,
        explicit_date = date_label,
        explicit_year = year,
    )
