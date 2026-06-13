"""Extrae metadatos EXIF de imágenes."""
from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import exifread
from PIL import Image

from core.quiet import quiet_stderr

# Silenciar el ruido de exifread ("File format not recognized.") en consola.
# El resultado se refleja igualmente en los flags de PhotoMetadata.
logging.getLogger("exifread").setLevel(logging.CRITICAL)


@dataclass
class PhotoMetadata:
    path: Path
    date_taken: Optional[datetime] = None
    year: str = "Sin_fecha"
    camera_make: str = ""
    camera_model: str = ""
    width: int = 0
    height: int = 0
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    file_size_kb: int = 0
    readable: bool = True          # False si Pillow no pudo abrir la imagen
    has_exif: bool = False         # True si se leyó algún tag EXIF
    error: Optional[str] = None    # descripción del problema, si lo hubo


def _dms_to_decimal(dms_values, ref: str) -> Optional[float]:
    """Convierte grados/minutos/segundos a decimal."""
    try:
        d = float(dms_values[0].num) / float(dms_values[0].den)
        m = float(dms_values[1].num) / float(dms_values[1].den)
        s = float(dms_values[2].num) / float(dms_values[2].den)
        decimal = d + m / 60 + s / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None


def extract_metadata(path: Path) -> PhotoMetadata:
    meta = PhotoMetadata(path=path)
    meta.file_size_kb = path.stat().st_size // 1024

    # — EXIF con exifread —
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="GPS GPSLongitude", details=False)

        if tags:
            meta.has_exif = True

        # Fecha
        for tag in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            if tag in tags:
                try:
                    meta.date_taken = datetime.strptime(str(tags[tag]), "%Y:%m:%d %H:%M:%S")
                    break
                except ValueError:
                    pass

        # Cámara
        if "Image Make" in tags:
            meta.camera_make = str(tags["Image Make"]).strip()
        if "Image Model" in tags:
            meta.camera_model = str(tags["Image Model"]).strip()

        # GPS
        if "GPS GPSLatitude" in tags and "GPS GPSLatitudeRef" in tags:
            meta.gps_lat = _dms_to_decimal(
                tags["GPS GPSLatitude"].values,
                str(tags["GPS GPSLatitudeRef"])
            )
        if "GPS GPSLongitude" in tags and "GPS GPSLongitudeRef" in tags:
            meta.gps_lon = _dms_to_decimal(
                tags["GPS GPSLongitude"].values,
                str(tags["GPS GPSLongitudeRef"])
            )
    except Exception:
        pass

    # — Dimensiones con Pillow (silenciando avisos C de libjpeg/libtiff) —
    try:
        with quiet_stderr():
            with Image.open(path) as img:
                meta.width, meta.height = img.size
    except Exception as e:
        meta.readable = False
        meta.error = f"Pillow no pudo abrir la imagen: {type(e).__name__}"

    # — Fallback de fecha: fecha de modificación del archivo —
    if meta.date_taken is None:
        try:
            mtime = path.stat().st_mtime
            meta.date_taken = datetime.fromtimestamp(mtime)
        except Exception:
            pass

    if meta.date_taken:
        meta.year = str(meta.date_taken.year)

    return meta
