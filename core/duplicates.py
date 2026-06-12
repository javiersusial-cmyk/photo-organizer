"""Detección de fotos duplicadas mediante hash perceptual."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

import imagehash
from PIL import Image


def compute_hash(path: Path) -> str | None:
    """Calcula el hash perceptual (pHash) de una imagen."""
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def find_duplicates(
    paths: List[Path], threshold: int = 10
) -> Dict[Path, Path]:
    """
    Compara todas las imágenes y devuelve un diccionario
    {duplicado: original} para cada foto identificada como duplicada.

    Se considera original la primera aparición (la de mayor tamaño
    en caso de empate de hash exacto).
    """
    hashes: List[Tuple[imagehash.ImageHash, Path]] = []
    duplicates: Dict[Path, Path] = {}

    for path in paths:
        try:
            with Image.open(path) as img:
                h = imagehash.phash(img)
        except Exception:
            continue

        # Buscar si ya existe un hash similar
        matched_original: Path | None = None
        for existing_hash, existing_path in hashes:
            if abs(h - existing_hash) <= threshold:
                matched_original = existing_path
                break

        if matched_original is not None:
            duplicates[path] = matched_original
        else:
            hashes.append((h, path))

    return duplicates
