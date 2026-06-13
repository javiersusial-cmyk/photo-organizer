"""
consolidate.py — Motor de consolidación de fotos (v2)

Filosofía:
  - Carpetas CON sentido (viaje, ciudad, evento...) → conservar nombre,
    asignar año, salida 'Año YYYY / Tipo - Nombre (fecha)'.
  - Carpetas SIN contexto (volcados de cámara) → IA: Personas / Naturaleza / Ciudades.
  - Duplicados exactos (nombre + metadatos) validados contra un catálogo SQLite único.
  - Multi-paso: cada ejecución valida contra el catálogo existente.

Uso:
    # Previsualizar sin copiar (RECOMENDADO primero)
    python consolidate.py --source "RUTA" --dest "DESTINO" --dry-run

    # Ejecutar de verdad
    python consolidate.py --source "RUTA" --dest "DESTINO"

    # Activar IA para volcados sin contexto
    python consolidate.py --source "RUTA" --dest "DESTINO" --ai

    # Fase Google (solo copia las que NO estén ya en el catálogo)
    python consolidate.py --source "RUTA_GOOGLE" --dest "DESTINO" --google --ai
"""
from __future__ import annotations

import argparse
import csv
import shutil
from collections import defaultdict, Counter
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from core.metadata import extract_metadata
from core.folder_context import analyze_folder
from core.catalog import Catalog

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tiff", ".tif", ".bmp",
              ".gif", ".webp", ".cr2", ".nef", ".arw"}


def sanitize(name: str) -> str:
    """Limpia un nombre para que sea válido como carpeta."""
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, " ")
    return " ".join(name.split()).strip(" .")


def group_by_leaf(source_root: Path) -> dict[Path, list[Path]]:
    """Agrupa las imágenes por la carpeta que las contiene."""
    groups: dict[Path, list[Path]] = defaultdict(list)
    for p in source_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            groups[p.parent].append(p)
    return groups


def build_dest_folder(dest_root: Path, year: str, tipo: str, nombre: str,
                      date_label: Optional[str]) -> Path:
    """Construye 'Año YYYY / Tipo - Nombre (fecha)'."""
    if date_label:
        sub = f"{tipo} - {nombre} ({date_label})"
    else:
        sub = f"{tipo} - {nombre} ({year})"
    return dest_root / f"Año {year}" / sanitize(sub)


def build_ai_folder(dest_root: Path, year: str, categoria: str,
                    ciudad: Optional[str]) -> Path:
    """Carpeta para fotos clasificadas por IA (Camino B)."""
    if categoria == "Ciudades" and ciudad:
        return dest_root / f"Año {year}" / "Ciudad" / sanitize(ciudad)
    return dest_root / f"Año {year}" / categoria


def main():
    ap = argparse.ArgumentParser(description="Consolidador de fotos v2")
    ap.add_argument("--source", required=True)
    ap.add_argument("--dest",   required=True)
    ap.add_argument("--catalog", default=None,
                    help="Ruta del catálogo SQLite (default: DEST/catalogo.db)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo previsualizar el mapeo, sin copiar ni registrar")
    ap.add_argument("--ai", action="store_true",
                    help="Usar IA para carpetas sin contexto (volcados)")
    ap.add_argument("--landmark-threshold", type=float, default=0.30,
                    help="Umbral de monumentos (más alto = menos falsos positivos)")
    ap.add_argument("--google", action="store_true",
                    help="Fase Google: solo copia fotos cuyo nombre NO esté en el catálogo")
    args = ap.parse_args()

    source_root = Path(args.source)
    dest_root   = Path(args.dest)
    catalog_path = Path(args.catalog) if args.catalog else dest_root / "catalogo.db"

    catalog = Catalog(catalog_path)
    print(f"Catálogo: {catalog_path}  ({catalog.count()} fotos registradas)")

    # Carpeta destino para fase Google
    google_root = dest_root / "Google fotos"

    # ── Escanear y agrupar ────────────────────────────────────────────────────
    print(f"\nEscaneando {source_root}...")
    groups = group_by_leaf(source_root)
    total = sum(len(v) for v in groups.values())
    print(f"  {total} imágenes en {len(groups)} carpetas")

    # IA perezosa (solo si se necesita)
    classifier = None

    def get_classifier():
        nonlocal classifier
        if classifier is None:
            from core.detector import TwoStepClassifier
            classifier = TwoStepClassifier(detect_landmarks=True)
        return classifier

    preview_rows: list[tuple] = []
    stats = Counter()
    copied = skipped_dup = skipped_google = 0

    for folder, photos in tqdm(groups.items(), unit="carpeta"):
        ctx = analyze_folder(folder, source_root)

        for src in photos:
            meta = extract_metadata(src)
            try:
                filesize = src.stat().st_size
            except OSError:
                filesize = 0
            dt_iso = meta.date_taken.isoformat() if meta.date_taken else None
            dup_key = Catalog.make_dup_key(src.name, filesize, dt_iso, meta.width, meta.height)

            # ── Fase Google: si el nombre ya existe en catálogo, descartar ──
            if args.google:
                if catalog.exists_by_filename(src.name):
                    skipped_google += 1
                    continue

            # ── Dedup exacto ──
            if not args.google and catalog.exists(dup_key):
                skipped_dup += 1
                continue

            # ── Decidir destino ──
            if ctx.meaningful:
                year = ctx.explicit_year or meta.year
                dest_dir = build_dest_folder(
                    google_root if args.google else dest_root,
                    year, ctx.tipo, ctx.nombre, ctx.explicit_date
                )
                categoria = f"{ctx.tipo} - {ctx.nombre}"
                ciudad = None
            else:
                # Camino B: IA
                if args.ai:
                    cat, ciudad = get_classifier().classify(
                        src, gps_city=None, hint_city=None
                    )
                    # Colapsar Familia→Personas y simplificar
                    if cat in ("Familia",):
                        cat = "Personas"
                else:
                    cat, ciudad = "Sin_clasificar", None
                year = meta.year
                dest_dir = build_ai_folder(
                    google_root if args.google else dest_root, year, cat, ciudad
                )
                categoria = cat

            dest_path = dest_dir / src.name
            stats[categoria.split(" - ")[0] if " - " in categoria else categoria] += 1

            preview_rows.append((
                str(src), str(dest_path), year, categoria,
                "Google" if args.google else ("IA" if not ctx.meaningful else "Carpeta")
            ))

            # ── Ejecutar (si no es dry-run) ──
            if not args.dry_run:
                origin = "google" if args.google else "principal"
                if catalog.add(
                    dup_key=dup_key, filename=src.name, filesize=filesize,
                    date_taken=dt_iso, year=year, width=meta.width, height=meta.height,
                    source_path=str(src), dest_path=str(dest_path),
                    category=categoria, origin=origin,
                ):
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    if not dest_path.exists():
                        shutil.copy2(src, dest_path)
                    copied += 1
                else:
                    skipped_dup += 1

    # ── Guardar preview ───────────────────────────────────────────────────────
    preview_csv = dest_root / ("preview_dryrun.csv" if args.dry_run else "ultima_ejecucion.csv")
    dest_root.mkdir(parents=True, exist_ok=True)
    with open(preview_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["origen", "destino", "año", "categoria", "via"])
        w.writerows(preview_rows)

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DRY-RUN (nada copiado)" if args.dry_run else "EJECUCIÓN COMPLETADA")
    print("=" * 60)
    print(f"  Fotos a procesar : {len(preview_rows)}")
    if not args.dry_run:
        print(f"  Copiadas         : {copied}")
        print(f"  Duplicadas (omitidas): {skipped_dup}")
    if args.google:
        print(f"  Google ya en catálogo (omitidas): {skipped_google}")
    print("\n  Distribución por categoría:")
    for cat, n in stats.most_common(30):
        print(f"    {cat:<35} {n:>6}")
    print(f"\n  Catálogo: {catalog.count()} fotos | Preview: {preview_csv}")
    print("=" * 60)

    catalog.close()


if __name__ == "__main__":
    main()
