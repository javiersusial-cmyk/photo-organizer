"""
Agrupa fotos de categoría Eventos en sub-eventos por proximidad temporal.

Si hay una brecha mayor a `gap_hours` entre fotos consecutivas (ordenadas
por fecha) → se considera un evento distinto.

Resultado: "Eventos/Evento_01", "Eventos/Evento_02", ...
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def group_events(
    paths_with_dates: list[tuple[Path, Optional[datetime]]],
    gap_hours: float = 12.0,
) -> dict[Path, str]:
    """
    Recibe una lista de (path, fecha) de fotos ya clasificadas como Eventos.
    Devuelve un dict {path: "Eventos/Evento_01"} con el sub-evento asignado.

    Fotos sin fecha van a "Eventos/Evento_sin_fecha".
    """
    # Separar las que tienen fecha de las que no
    with_date    = [(p, d) for p, d in paths_with_dates if d is not None]
    without_date = [p for p, d in paths_with_dates if d is None]

    # Ordenar por fecha
    with_date.sort(key=lambda x: x[1])

    result: dict[Path, str] = {}
    gap = timedelta(hours=gap_hours)
    event_num   = 0
    last_date: Optional[datetime] = None

    for path, date in with_date:
        if last_date is None or (date - last_date) > gap:
            event_num += 1
        result[path] = f"Eventos/Evento_{event_num:02d}"
        last_date = date

    for path in without_date:
        result[path] = "Eventos/Evento_sin_fecha"

    return result
