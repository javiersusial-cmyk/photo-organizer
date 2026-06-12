"""
Sistema de checkpoint para reanudar procesos interrumpidos.

El fichero checkpoint.json se guarda en la carpeta destino y contiene:
  - metadata:   {ruta: {year, camera, gps_lat, gps_lon, date_taken, ...}}
  - duplicates: {ruta_duplicada: ruta_original}
  - categories: {ruta: categoria}
  - cities:     {ruta: ciudad}
  - copied:     {ruta_origen: ruta_destino}
  - phases_done: lista de fases completadas
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CHECKPOINT_FILE = "checkpoint.json"


class Checkpoint:
    def __init__(self, dest_root: Path):
        self._path = dest_root / CHECKPOINT_FILE
        self._data: dict[str, Any] = {
            "phases_done": [],
            "metadata":    {},
            "duplicates":  {},
            "categories":  {},
            "cities":      {},
            "copied":      {},
        }
        dest_root.mkdir(parents=True, exist_ok=True)

    def load(self) -> bool:
        """Carga el checkpoint si existe. Devuelve True si había datos."""
        if not self._path.exists():
            return False
        try:
            with open(self._path, encoding="utf-8") as f:
                self._data = json.load(f)
            phases = self._data.get("phases_done", [])
            print(f"  Checkpoint encontrado. Fases completadas: {phases}")
            return True
        except Exception as e:
            print(f"  Advertencia: no se pudo leer el checkpoint ({e}). Empezando desde cero.")
            return False

    def save(self):
        """Persiste el checkpoint en disco."""
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False)
        tmp.replace(self._path)  # escritura atómica

    def phase_done(self, phase: str) -> bool:
        return phase in self._data.get("phases_done", [])

    def mark_phase_done(self, phase: str):
        if phase not in self._data["phases_done"]:
            self._data["phases_done"].append(phase)
        self.save()

    # ── Metadata ─────────────────────────────────────────────────────────────

    def set_metadata(self, path: Path, record: dict):
        self._data["metadata"][str(path)] = record

    def get_metadata(self) -> dict[str, dict]:
        return self._data.get("metadata", {})

    def metadata_done_paths(self) -> set[str]:
        return set(self._data.get("metadata", {}).keys())

    # ── Duplicates ───────────────────────────────────────────────────────────

    def set_duplicates(self, duplicates: dict[Path, Path]):
        self._data["duplicates"] = {str(k): str(v) for k, v in duplicates.items()}

    def get_duplicates(self) -> dict[str, str]:
        return self._data.get("duplicates", {})

    # ── Categories / Cities ──────────────────────────────────────────────────

    def set_category(self, path: Path, category: str):
        self._data["categories"][str(path)] = category

    def set_city(self, path: Path, city: str | None):
        if city:
            self._data["cities"][str(path)] = city

    def get_categories(self) -> dict[str, str]:
        return self._data.get("categories", {})

    def get_cities(self) -> dict[str, str]:
        return self._data.get("cities", {})

    def classified_paths(self) -> set[str]:
        return set(self._data.get("categories", {}).keys())

    # ── Copied ───────────────────────────────────────────────────────────────

    def set_copied(self, src: Path, dest: Path):
        self._data["copied"][str(src)] = str(dest)

    def get_copied(self) -> dict[str, str]:
        return self._data.get("copied", {})

    def is_copied(self, src: Path) -> bool:
        return str(src) in self._data.get("copied", {})

    def delete(self):
        """Elimina el checkpoint al finalizar correctamente."""
        if self._path.exists():
            self._path.unlink()
            print("  Checkpoint eliminado (proceso completado con éxito).")
