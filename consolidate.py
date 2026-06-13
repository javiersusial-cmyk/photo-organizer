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

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".tif",
              ".bmp", ".gif", ".webp",
              # RAW de distintas marcas
              ".cr2", ".cr3", ".nef", ".arw", ".dng", ".pef", ".raf",
              ".orf", ".rw2", ".srw", ".raw", ".x3f"}


def sanitize(name: str) -> str:
    """Limpia un nombre para que sea válido como carpeta."""
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, " ")
    return " ".join(name.split()).strip(" .")


def unique_path(dest: Path) -> Path:
    """Devuelve una ruta libre añadiendo sufijo _N si ya existe."""
    if not dest.exists():
        return dest
    stem, suffix, n = dest.stem, dest.suffix, 1
    while True:
        cand = dest.parent / f"{stem}_{n}{suffix}"
        if not cand.exists():
            return cand
        n += 1


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


def build_session_map(photos: list[Path], gap_hours: float = 12.0) -> dict[Path, str]:
    """
    Para una carpeta SIN contexto, agrupa las fotos por proximidad temporal
    en sesiones. Devuelve {foto: etiqueta_sesion} donde la etiqueta es la
    fecha (o rango de fechas) de la sesión.
    """
    from datetime import timedelta
    dated   = []
    undated = []
    for p in photos:
        meta = extract_metadata(p)
        if meta.date_taken:
            dated.append((p, meta.date_taken))
        else:
            undated.append(p)

    dated.sort(key=lambda x: x[1])
    result: dict[Path, str] = {}
    gap = timedelta(hours=gap_hours)

    session: list = []
    sessions: list[list] = []
    last = None
    for p, dt in dated:
        if last is not None and (dt - last) > gap:
            sessions.append(session)
            session = []
        session.append((p, dt))
        last = dt
    if session:
        sessions.append(session)

    MIN_SESSION = 5   # sesiones con menos fotos van a 'resto'
    for grp in sessions:
        if len(grp) < MIN_SESSION:
            for p, _dt in grp:
                result[p] = "resto"
            continue
        d0 = grp[0][1].date()
        d1 = grp[-1][1].date()
        label = f"{d0:%Y-%m-%d}" if d0 == d1 else f"{d0:%Y-%m-%d} a {d1:%Y-%m-%d}"
        for p, _dt in grp:
            result[p] = label

    for p in undated:
        result[p] = "resto"

    return result


def main():
    ap = argparse.ArgumentParser(description="Consolidador de fotos v2")
    ap.add_argument("--source", required=True)
    ap.add_argument("--dest",   required=True)
    ap.add_argument("--catalog", default=None,
                    help="Ruta del catálogo SQLite (default: DEST/catalogo.db)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo previsualizar el mapeo, sin copiar ni registrar")
    ap.add_argument("--ai", action="store_true",
                    help="Usar IA para carpetas sin contexto (en vez de agrupar por fecha)")
    ap.add_argument("--session-gap", type=float, default=12.0,
                    help="Horas de separación para una nueva sesión en 'Sin clasificar' (default: 12)")
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
    copied = skipped_google = dup_to_review = 0
    seen_keys: set[str] = set()   # claves ya colocadas en esta ejecución

    for folder, photos in tqdm(groups.items(), unit="carpeta"):
        ctx = analyze_folder(folder, source_root)

        # Para carpetas sin contexto y sin IA: precalcular sesiones por fecha
        session_map: dict[Path, str] = {}
        if not ctx.meaningful and not args.ai:
            session_map = build_session_map(photos, gap_hours=args.session_gap)

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

            # ── Dedup exacto → llevar la copia a Duplicadas/ para revisión ──
            if not args.google and (dup_key in seen_keys or catalog.exists(dup_key)):
                year = meta.year
                dup_dir  = dest_root / "Duplicadas" / f"Año {year}"
                dup_dest = dup_dir / src.name
                preview_rows.append((str(src), str(dup_dest), year, "Duplicada", "Duplicada"))
                stats["Duplicada"] += 1
                dup_to_review += 1
                if not args.dry_run and not catalog.duplicate_seen(str(src)):
                    dup_dir.mkdir(parents=True, exist_ok=True)
                    final = unique_path(dup_dest)
                    shutil.copy2(src, final)
                    catalog.add_duplicate(str(src), dup_key, str(final))
                continue

            seen_keys.add(dup_key)

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
                year   = meta.year
                target = google_root if args.google else dest_root
                if args.ai:
                    # Camino B con IA visual
                    cat, ciudad = get_classifier().classify(
                        src, gps_city=None, hint_city=None
                    )
                    if cat == "Familia":
                        cat = "Personas"
                    dest_dir  = build_ai_folder(target, year, cat, ciudad)
                    categoria = cat
                else:
                    # Camino B por sesión temporal → Sin clasificar / <fecha>
                    sesion    = session_map.get(src, "sin fecha")
                    dest_dir  = target / f"Año {year}" / "Sin clasificar" / sanitize(sesion)
                    categoria = "Sin_clasificar"

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

    # ── Guardar preview ───────────────────────────────────────────────────────
    base_name = "preview_dryrun" if args.dry_run else "ultima_ejecucion"
    preview_csv = dest_root / f"{base_name}.csv"
    dest_root.mkdir(parents=True, exist_ok=True)

    def _write_csv(path: Path) -> bool:
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["origen", "destino", "año", "categoria", "via"])
                w.writerows(preview_rows)
            return True
        except PermissionError:
            return False

    if not _write_csv(preview_csv):
        # Fichero bloqueado (abierto en Excel) → escribir con marca de tiempo
        from datetime import datetime as _dt
        alt = dest_root / f"{base_name}_{_dt.now():%Y%m%d_%H%M%S}.csv"
        if _write_csv(alt):
            print(f"\n  AVISO: '{preview_csv.name}' estaba bloqueado (¿abierto en Excel?).")
            print(f"  Preview guardado en: {alt.name}")
            preview_csv = alt
        else:
            print(f"\n  AVISO: no se pudo escribir el preview CSV (sin permisos).")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DRY-RUN (nada copiado)" if args.dry_run else "EJECUCIÓN COMPLETADA")
    print("=" * 60)
    print(f"  Fotos a procesar : {len(preview_rows)}")
    print(f"  Duplicadas -> carpeta Duplicadas/ : {dup_to_review}")
    if not args.dry_run:
        print(f"  Copiadas         : {copied}")
    if args.google:
        print(f"  Google ya en catálogo (omitidas): {skipped_google}")
    print("\n  Distribución por categoría:")
    for cat, n in stats.most_common(30):
        print(f"    {cat:<35} {n:>6}")
    print(f"\n  Catálogo: {catalog.count()} fotos | "
          f"Duplicadas registradas: {catalog.count_duplicates()} | Preview: {preview_csv}")
    print("=" * 60)

    catalog.close()


if __name__ == "__main__":
    main()
