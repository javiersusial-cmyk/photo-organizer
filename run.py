"""
photo-organizer — CLI principal con soporte de checkpoint/rearranque

Uso:
    python run.py --source ./mis_fotos --dest ./fotos_organizadas
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --no-classify
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --no-duplicates
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --only-inventory
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --reset
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --cluster
    python run.py --source ./mis_fotos --dest ./fotos_organizadas --delete-source

Si el proceso se interrumpe, al relanzar con los mismos argumentos
continúa desde la última fase completada.
Usa --reset para empezar desde cero ignorando el checkpoint.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from tqdm import tqdm

from core.scanner import scan_images
from core.metadata import extract_metadata, PhotoMetadata
from core.duplicates import find_duplicates
from core.classifier import PhotoClassifier
from core.organizer import build_dest_path, copy_photo
from core.geocoder import coords_to_city
from core.folder_hints import extract_folder_hints
from core.event_grouper import group_events
from core.clustering import VisualClusterer
from core.checkpoint import Checkpoint
from reports.inventory import InventoryRow, save_inventory


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def meta_to_dict(meta: PhotoMetadata) -> dict:
    return {
        "date_taken":   meta.date_taken.isoformat() if meta.date_taken else None,
        "year":         meta.year,
        "camera_make":  meta.camera_make,
        "camera_model": meta.camera_model,
        "width":        meta.width,
        "height":       meta.height,
        "gps_lat":      meta.gps_lat,
        "gps_lon":      meta.gps_lon,
        "file_size_kb": meta.file_size_kb,
    }


def dict_to_meta(path: Path, d: dict) -> PhotoMetadata:
    meta = PhotoMetadata(path=path)
    meta.year         = d.get("year", "Sin_fecha")
    meta.camera_make  = d.get("camera_make", "")
    meta.camera_model = d.get("camera_model", "")
    meta.width        = d.get("width", 0)
    meta.height       = d.get("height", 0)
    meta.gps_lat      = d.get("gps_lat")
    meta.gps_lon      = d.get("gps_lon")
    meta.file_size_kb = d.get("file_size_kb", 0)
    dt = d.get("date_taken")
    if dt:
        try:
            meta.date_taken = datetime.fromisoformat(dt)
        except ValueError:
            pass
    return meta


def resolve_category_and_city(
    clip_category: str,
    hints_category: Optional[str],
    hints_city: Optional[str],
    gps_city: Optional[str],
    fallback: str,
) -> tuple[str, Optional[str]]:
    """
    Prioridad: hint carpeta > CLIP > fallback.
    El GPS aporta la ciudad pero NO fuerza la categoría Viajes.
    Solo se usa como ciudad si CLIP ya clasificó la foto como Viajes,
    o si el hint de carpeta indica Viajes.
    """
    # 1. Carpeta origen ya organizada — máxima confianza
    if hints_category:
        city = hints_city or (gps_city if hints_category == "Viajes" else None)
        return hints_category, city

    # 2. CLIP decide la categoría; GPS enriquece con ciudad si es Viajes
    if clip_category and clip_category != fallback:
        city = gps_city if clip_category == "Viajes" else None
        return clip_category, city

    # 3. Fallback — si tiene GPS al menos ponemos la ciudad en Sin_clasificar
    return fallback, None


def main():
    parser = argparse.ArgumentParser(
        description="Organiza fotos por año y temática, detecta duplicados y genera inventario."
    )
    parser.add_argument("--source",       required=True, help="Carpeta origen con las fotos")
    parser.add_argument("--dest",         required=True, help="Carpeta destino organizada")
    parser.add_argument("--config",       default="config.yaml")
    parser.add_argument("--no-classify",  action="store_true", help="Omitir clasificación CLIP")
    parser.add_argument("--no-duplicates",action="store_true", help="Omitir detección de duplicados")
    parser.add_argument("--no-gps",        action="store_true", help="Omitir geocodificación GPS")
    parser.add_argument("--event-gap",     type=float, default=12.0,
                        help="Horas de brecha para considerar un evento distinto (default: 12)")
    parser.add_argument("--only-inventory",action="store_true", help="Solo inventario, sin copiar")
    parser.add_argument("--reset",        action="store_true", help="Ignorar checkpoint y empezar desde cero")
    parser.add_argument(
        "--cluster", action="store_true",
        help="Activar clustering visual CLIP+DBSCAN para fotos sin GPS ni pista de carpeta"
    )
    parser.add_argument(
        "--cluster-eps", type=float, default=0.35,
        help="Sensibilidad del clustering: menor=clusters más compactos (default: 0.35)"
    )
    parser.add_argument(
        "--cluster-min", type=int, default=3,
        help="Mínimo de fotos para formar un cluster (default: 3)"
    )
    parser.add_argument(
        "--delete-source", action="store_true",
        help="ELIMINAR la carpeta origen tras copiar correctamente todas las fotos"
    )
    args = parser.parse_args()

    cfg         = load_config(args.config)
    source_root = Path(args.source)
    dest_root   = Path(args.dest)
    fallback    = cfg.get("fallback_category", "Sin_clasificar")

    # ── Checkpoint ───────────────────────────────────────────────────────────
    ckpt = Checkpoint(dest_root)
    if args.reset:
        print("  --reset: ignorando checkpoint previo.")
    else:
        ckpt.load()

    # ── 1. Escanear ──────────────────────────────────────────────────────────
    print(f"\n[1/5] Escaneando fotos en: {args.source}")
    images = scan_images(args.source, cfg["extensions"])
    print(f"      {len(images)} imágenes encontradas")
    if not images:
        print("No se encontraron imágenes.")
        sys.exit(0)

    # ── 2. Metadatos + hints de carpeta ──────────────────────────────────────
    print("\n[2/5] Extrayendo metadatos EXIF y analizando carpetas...")
    done_paths  = ckpt.metadata_done_paths()
    pending     = [p for p in images if str(p) not in done_paths]
    already     = len(images) - len(pending)
    if already:
        print(f"      {already} fotos ya procesadas (checkpoint). Procesando {len(pending)} restantes...")

    metadata_map: dict[Path, PhotoMetadata] = {}
    hints_map:    dict[Path, object]        = {}

    # Restaurar metadatos ya guardados
    for str_path, record in ckpt.get_metadata().items():
        p = Path(str_path)
        metadata_map[p] = dict_to_meta(p, record)
        hints_map[p]    = extract_folder_hints(p, source_root)

    # Procesar pendientes
    for path in tqdm(pending, unit="foto"):
        meta = extract_metadata(path)
        metadata_map[path] = meta
        hints_map[path]    = extract_folder_hints(path, source_root)
        ckpt.set_metadata(path, meta_to_dict(meta))

    if pending:
        ckpt.mark_phase_done("metadata")
    print(f"      Metadatos completados.")

    # ── 3. Duplicados ────────────────────────────────────────────────────────
    duplicates: dict[Path, Path] = {}
    if not args.no_duplicates:
        if ckpt.phase_done("duplicates"):
            print("\n[3/5] Duplicados (checkpoint) — restaurando...")
            for k, v in ckpt.get_duplicates().items():
                duplicates[Path(k)] = Path(v)
            print(f"      {len(duplicates)} duplicados restaurados")
        else:
            print("\n[3/5] Detectando duplicados (hash perceptual)...")
            duplicates = find_duplicates(images, threshold=cfg.get("duplicate_threshold", 10))
            print(f"      {len(duplicates)} duplicados detectados")
            ckpt.set_duplicates(duplicates)
            ckpt.mark_phase_done("duplicates")
    else:
        print("\n[3/5] Detección de duplicados omitida")

    # ── 4. Clasificar (CLIP + GPS + hints) ───────────────────────────────────
    print("\n[4/5] Clasificando imágenes...")

    # 4a. CLIP
    clip_map: dict[Path, str] = {}
    if not args.no_classify:
        classified = ckpt.classified_paths()
        pending_clip = [p for p in images if str(p) not in classified and p not in duplicates]
        already_clip = len(images) - len(duplicates) - len(pending_clip)

        # Restaurar clasificaciones previas
        for str_path, cat in ckpt.get_categories().items():
            clip_map[Path(str_path)] = cat

        if already_clip > 0:
            print(f"  → CLIP: {already_clip} ya clasificadas (checkpoint). Clasificando {len(pending_clip)} restantes...")
        else:
            print(f"  → Clasificación temática con CLIP ({len(pending_clip)} fotos)...")

        if pending_clip:
            classifier = PhotoClassifier(categories=cfg["categories"], fallback=fallback)
            for path in tqdm(pending_clip, unit="foto"):
                cat = classifier.classify(path)
                clip_map[path] = cat
                ckpt.set_category(path, cat)
                # Guardar cada 500 fotos para no perder demasiado progreso
                if len(clip_map) % 500 == 0:
                    ckpt.save()
            ckpt.save()

        for path in duplicates:
            clip_map[path] = fallback
    else:
        print("  → Clasificación CLIP omitida")
        for path in images:
            clip_map[path] = fallback

    # 4b. GPS → ciudad
    gps_city_map: dict[Path, str] = {}
    if not args.no_gps:
        # Restaurar ciudades del checkpoint
        for str_path, city in ckpt.get_cities().items():
            gps_city_map[Path(str_path)] = city

        pending_gps = [
            p for p in images
            if str(p) not in ckpt.get_cities()
            and metadata_map[p].gps_lat is not None
        ]
        if pending_gps:
            print(f"  → Geocodificación GPS ({len(pending_gps)} fotos con coordenadas)...")
            for path in tqdm(pending_gps, unit="foto"):
                meta = metadata_map[path]
                city = coords_to_city(meta.gps_lat, meta.gps_lon)
                if city:
                    gps_city_map[path] = city
                    ckpt.set_city(path, city)
            ckpt.save()
        total_gps = len(gps_city_map)
        print(f"      {total_gps} fotos con ciudad detectada por GPS")

    # 4c. Combinar categoría base
    category_map: dict[Path, str]           = {}
    city_map:     dict[Path, Optional[str]] = {}
    for path in images:
        hints = hints_map[path]
        category, city = resolve_category_and_city(
            clip_category  = clip_map.get(path, fallback),
            hints_category = hints.category,
            hints_city     = hints.city,
            gps_city       = gps_city_map.get(path),
            fallback       = fallback,
        )
        category_map[path] = category
        city_map[path]     = city

    # 4d. Clustering visual para fotos sin clasificación fiable
    if args.cluster:
        # Solo se clusterizan fotos que han caído en fallback y no tienen GPS ni hint
        to_cluster = [
            p for p in images
            if p not in duplicates
            and category_map[p] == fallback
            and p not in gps_city_map
            and not hints_map[p].category
        ]
        if to_cluster:
            print(f"\n  → Clustering visual ({len(to_cluster)} fotos sin clasificar)...")
            clusterer = VisualClusterer(
                categories  = cfg["categories"],
                fallback    = fallback,
                eps         = args.cluster_eps,
                min_samples = args.cluster_min,
            )
            cluster_result = clusterer.cluster(to_cluster)
            for path, cat in cluster_result.items():
                category_map[path] = cat
                city_map[path]     = None
        else:
            print("  → Clustering: no hay fotos sin clasificar, omitido.")

    # 4e. Agrupar Eventos en sub-eventos por proximidad temporal
    print(f"  → Agrupando eventos (brecha {args.event_gap}h)...")
    event_paths = [
        (p, metadata_map[p].date_taken)
        for p in images
        if category_map[p] == "Eventos" and p not in duplicates
    ]
    if event_paths:
        event_groups = group_events(event_paths, gap_hours=args.event_gap)
        for path, sub_cat in event_groups.items():
            category_map[path] = sub_cat
        unique_events = len({v for v in event_groups.values()})
        print(f"      {len(event_paths)} fotos de eventos → {unique_events} eventos distintos")

    # ── 5. Copiar y generar inventario ───────────────────────────────────────
    print("\n[5/5] Copiando fotos y generando inventario...")
    already_copied = ckpt.get_copied()
    inventory_rows: list[InventoryRow] = []
    copied_count   = 0
    skipped_count  = 0

    for path in tqdm(images, unit="foto"):
        meta     = metadata_map[path]
        hints    = hints_map[path]
        category = category_map[path]
        city     = city_map[path]
        is_dup   = path in duplicates
        original = duplicates.get(path)
        year     = hints.year or meta.year

        dest_path = build_dest_path(
            dest_root         = dest_root,
            year              = year,
            category          = category,
            city              = city,
            original_path     = path,
            is_duplicate      = is_dup,
            duplicates_folder = cfg.get("duplicates_folder", "_Duplicados"),
        )

        final_dest = ""
        if not args.only_inventory:
            if ckpt.is_copied(path):
                # Ya copiada en una ejecución anterior
                final_dest = already_copied[str(path)]
                skipped_count += 1
            elif not is_dup or cfg.get("copy_duplicates", True):
                final_dest = str(copy_photo(path, dest_path))
                ckpt.set_copied(path, Path(final_dest))
                copied_count += 1
                # Guardar checkpoint cada 200 copias
                if copied_count % 200 == 0:
                    ckpt.save()
        else:
            final_dest = str(dest_path)

        tematica_full = f"Viajes/{city}" if category == "Viajes" and city else category
        inventory_rows.append(InventoryRow(
            archivo_origen  = str(path),
            nombre          = path.name,
            extension       = path.suffix.lower(),
            fecha_toma      = meta.date_taken.strftime("%Y-%m-%d %H:%M:%S") if meta.date_taken else "",
            año             = year,
            camara          = f"{meta.camera_make} {meta.camera_model}".strip(),
            resolucion      = f"{meta.width}x{meta.height}" if meta.width else "",
            gps_lat         = str(meta.gps_lat) if meta.gps_lat is not None else "",
            gps_lon         = str(meta.gps_lon) if meta.gps_lon is not None else "",
            tematica        = tematica_full,
            duplicado_de    = str(original) if original else "",
            archivo_destino = final_dest,
            tamaño_kb       = meta.file_size_kb,
        ))

    ckpt.save()
    if skipped_count:
        print(f"      {skipped_count} fotos ya copiadas en ejecución anterior, {copied_count} nuevas.")

    base_name = source_root.name or "fotos"
    save_inventory(inventory_rows, dest_root, base_name)

    # Eliminar checkpoint solo si todo fue bien y no es solo inventario
    if not args.only_inventory:
        ckpt.delete()

    # ── Borrar carpeta origen (opcional, requiere confirmación) ───────────────
    if args.delete_source and not args.only_inventory:
        import shutil
        print(f"\n  ATENCIÓN: Se va a eliminar la carpeta origen: {source_root.resolve()}")
        confirm = input("  Escribe 'BORRAR' para confirmar (cualquier otra cosa cancela): ").strip()
        if confirm == "BORRAR":
            shutil.rmtree(source_root)
            print(f"  Carpeta origen eliminada: {source_root}")
        else:
            print("  Borrado cancelado.")

    # ── Resumen ──────────────────────────────────────────────────────────────
    unique_rows = [r for r in inventory_rows if not r.duplicado_de]
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Total fotos procesadas : {len(images)}")
    print(f"  Duplicados detectados  : {len(duplicates)}")
    print(f"  Fotos únicas           : {len(unique_rows)}")

    cat_counts = Counter(r.tematica for r in unique_rows)
    print("\n  Distribución por temática:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"    {cat:<30} {count:>5} fotos")

    year_counts = Counter(r.año for r in unique_rows)
    print("\n  Distribución por año:")
    for year, count in sorted(year_counts.items()):
        print(f"    {year:<10} {count:>5} fotos")

    print(f"\n  Destino: {dest_root.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
