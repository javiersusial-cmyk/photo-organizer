"""Copia fotos al destino organizado por año y categoría."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional


def build_dest_path(
    dest_root: Path,
    year: str,
    category: str,
    city: Optional[str],
    original_path: Path,
    is_duplicate: bool,
    duplicates_folder: str,
) -> Path:
    """
    Calcula la ruta de destino para una foto.

    Estructura resultante:
      - Duplicado  → dest/_Duplicados/AÑO/fichero
      - Viaje+ciudad → dest/AÑO/Viajes/Ciudad/fichero
      - Resto      → dest/AÑO/Categoria/fichero
    """
    if is_duplicate:
        folder = dest_root / duplicates_folder / year
    elif category == "Viajes" and city:
        folder = dest_root / year / "Viajes" / city
    elif category == "Ciudades" and city:
        folder = dest_root / year / "Ciudades" / city
    elif "/" in category:
        # Sub-categoría ya incluye la barra, ej: "Eventos/Evento_01"
        parts = category.split("/", 1)
        folder = dest_root / year / parts[0] / parts[1]
    else:
        folder = dest_root / year / category

    return folder / original_path.name


def copy_photo(src: Path, dest: Path) -> Path:
    """
    Copia src a dest. Si ya existe un archivo con el mismo nombre
    añade un sufijo numérico para evitar colisiones.
    Devuelve la ruta final donde se copió.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if not dest.exists():
        shutil.copy2(src, dest)
        return dest

    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    while True:
        new_dest = dest.parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            shutil.copy2(src, new_dest)
            return new_dest
        counter += 1
