"""
buscar.py — Consulta dónde va (o fue) una foto, por nombre o parte del nombre.

Busca en:
  1. El preview de la última ejecución (preview_dryrun.csv / ultima_ejecucion.csv)
  2. El catálogo SQLite (fotos colocadas + duplicadas)

Uso:
    python buscar.py --dest "C:\\Fotos catalogadas" IMGP0334
    python buscar.py --dest "C:\\Fotos catalogadas" _IGP1032.DNG
    python buscar.py --dest "C:\\Fotos catalogadas" sudafrica
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def buscar_en_csv(csv_path: Path, termino: str) -> list[tuple]:
    if not csv_path.exists():
        return []
    out = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) >= 5 and termino.lower() in row[0].lower():
                out.append((row[0], row[1], row[4]))   # origen, destino, via
    return out


def buscar_en_catalogo(db_path: Path, termino: str) -> tuple[list, list]:
    if not db_path.exists():
        return [], []
    con = sqlite3.connect(str(db_path))
    like = f"%{termino.lower()}%"
    fotos = con.execute(
        "SELECT source_path, dest_path, category, year FROM photos "
        "WHERE lower(source_path) LIKE ? OR filename LIKE ?",
        (like, like)
    ).fetchall()
    dups = con.execute(
        "SELECT source_path, dup_dest FROM duplicates WHERE lower(source_path) LIKE ?",
        (like,)
    ).fetchall()
    con.close()
    return fotos, dups


def main():
    ap = argparse.ArgumentParser(description="Consulta el destino de una foto")
    ap.add_argument("--dest", required=True, help="Carpeta destino (donde está catalogo.db)")
    ap.add_argument("termino", help="Nombre o parte del nombre de la foto")
    args = ap.parse_args()

    dest = Path(args.dest)
    print(f"\nBuscando '{args.termino}' en {dest}\n" + "-" * 60)

    # 1. Preview
    for nombre in ("preview_dryrun.csv", "ultima_ejecucion.csv"):
        res = buscar_en_csv(dest / nombre, args.termino)
        if res:
            print(f"\n[Preview: {nombre}]")
            for origen, destino, via in res:
                print(f"  {origen}")
                print(f"    -> {destino}  [{via}]")

    # 2. Catálogo
    fotos, dups = buscar_en_catalogo(dest / "catalogo.db", args.termino)
    if fotos:
        print(f"\n[Catálogo: fotos colocadas]")
        for origen, destino, cat, year in fotos:
            print(f"  {origen}")
            print(f"    -> {destino}  ({cat}, {year})")
    if dups:
        print(f"\n[Catálogo: duplicadas]")
        for origen, destino in dups:
            print(f"  {origen}")
            print(f"    -> {destino}")

    if not any([fotos, dups]) and not any(
        (dest / n).exists() for n in ("preview_dryrun.csv", "ultima_ejecucion.csv")
    ):
        print("  No hay preview ni catálogo en esa carpeta destino.")
    print("-" * 60)


if __name__ == "__main__":
    main()
