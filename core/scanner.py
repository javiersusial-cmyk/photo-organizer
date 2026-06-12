"""Recorre carpetas y devuelve lista de rutas de imágenes."""
from pathlib import Path
from typing import List


def scan_images(source_dir: str, extensions: List[str]) -> List[Path]:
    """Devuelve todas las imágenes bajo source_dir con las extensiones indicadas."""
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(f"Carpeta origen no encontrada: {source_dir}")

    ext_set = {e.lower() for e in extensions}
    images = [
        p for p in source.rglob("*")
        if p.is_file() and p.suffix.lower() in ext_set
    ]
    return sorted(images)
