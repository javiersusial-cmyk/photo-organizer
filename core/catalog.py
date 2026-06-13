"""
Catálogo único de fotos en SQLite.

Un solo fichero .db que registra cada foto ya colocada en el destino.
Permite deduplicar entre ejecuciones (multi-paso): antes de copiar una
foto se comprueba si su clave ya existe en el catálogo.

Clave de duplicado = mismo nombre + mismos metadatos (NO perceptual):
    nombre_fichero (minúsculas) + tamaño_bytes + fecha_toma + ancho + alto

El catálogo es la fuente de verdad persistente del sistema.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class Catalog:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_schema()

    def _create_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                dup_key      TEXT UNIQUE NOT NULL,
                filename     TEXT NOT NULL,
                filesize     INTEGER,
                date_taken   TEXT,
                year         TEXT,
                width        INTEGER,
                height       INTEGER,
                source_path  TEXT NOT NULL,
                dest_path    TEXT,
                category     TEXT,
                origin       TEXT DEFAULT 'principal',  -- 'principal' | 'google'
                added_at     TEXT NOT NULL
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_dupkey ON photos(dup_key)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_filename ON photos(filename)")
        self._conn.commit()

    @staticmethod
    def make_dup_key(filename: str, filesize: int, date_taken: Optional[str],
                     width: int, height: int) -> str:
        """Clave de duplicado exacta: nombre + metadatos (no brillo/perceptual)."""
        name = filename.strip().lower()
        dt   = date_taken or ""
        return f"{name}|{filesize}|{dt}|{width}x{height}"

    def exists(self, dup_key: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM photos WHERE dup_key = ? LIMIT 1", (dup_key,))
        return cur.fetchone() is not None

    def exists_by_filename(self, filename: str) -> bool:
        """Comprobación más laxa: solo por nombre (para la fase Google)."""
        cur = self._conn.execute(
            "SELECT 1 FROM photos WHERE filename = ? LIMIT 1", (filename.strip().lower(),)
        )
        return cur.fetchone() is not None

    def add(self, *, dup_key: str, filename: str, filesize: int,
            date_taken: Optional[str], year: str, width: int, height: int,
            source_path: str, dest_path: str, category: str,
            origin: str = "principal") -> bool:
        """Registra una foto. Devuelve False si ya existía (clave duplicada)."""
        try:
            self._conn.execute("""
                INSERT INTO photos
                  (dup_key, filename, filesize, date_taken, year, width, height,
                   source_path, dest_path, category, origin, added_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                dup_key, filename.strip().lower(), filesize, date_taken, year,
                width, height, source_path, dest_path, category, origin,
                datetime.now().isoformat(timespec="seconds"),
            ))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # clave ya existente

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]

    def stats_by_category(self) -> list[tuple[str, int]]:
        cur = self._conn.execute(
            "SELECT category, COUNT(*) FROM photos GROUP BY category ORDER BY 2 DESC"
        )
        return cur.fetchall()

    def export_csv(self, csv_path: str | Path):
        """Exporta el catálogo completo a CSV para consulta."""
        import csv
        cur = self._conn.execute("""
            SELECT filename, year, category, date_taken, width, height,
                   filesize, origin, source_path, dest_path, added_at
            FROM photos ORDER BY year, category, filename
        """)
        cols = [d[0] for d in cur.description]
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(cur.fetchall())

    def close(self):
        self._conn.close()
