"""Genera el inventario de fotos en formato CSV y Excel."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd


@dataclass
class InventoryRow:
    archivo_origen: str
    nombre: str
    extension: str
    fecha_toma: str
    año: str
    camara: str
    resolucion: str
    gps_lat: str
    gps_lon: str
    tematica: str
    duplicado_de: str
    archivo_destino: str
    tamaño_kb: int


def save_inventory(rows: List[InventoryRow], output_dir: Path, base_name: str) -> None:
    """Guarda el inventario como CSV y Excel en output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    records = [
        {
            "Archivo origen":   r.archivo_origen,
            "Nombre":           r.nombre,
            "Extensión":        r.extension,
            "Fecha de toma":    r.fecha_toma,
            "Año":              r.año,
            "Cámara":           r.camara,
            "Resolución":       r.resolucion,
            "GPS Latitud":      r.gps_lat,
            "GPS Longitud":     r.gps_lon,
            "Temática":         r.tematica,
            "Duplicado de":     r.duplicado_de,
            "Archivo destino":  r.archivo_destino,
            "Tamaño (KB)":      r.tamaño_kb,
        }
        for r in rows
    ]

    df = pd.DataFrame(records)

    csv_path = output_dir / f"{base_name}_inventario.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  Inventario CSV  → {csv_path}")

    xlsx_path = output_dir / f"{base_name}_inventario.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventario")

        # Autoajustar ancho de columnas
        ws = writer.sheets["Inventario"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    print(f"  Inventario Excel → {xlsx_path}")
