"""
Genera automáticamente el diccionario FOLDER_CITY_KEYWORDS en core/geocoder.py
a partir de los datos públicos de GeoNames (geonames.org).

Descarga los ficheros de municipios de los países indicados, filtra por
población mínima y genera todas las variantes de nombre (nombre oficial,
nombre ASCII, nombres alternativos en español e inglés).

Uso:
    python tools/generate_city_dict.py
    python tools/generate_city_dict.py --min-pop 1000
    python tools/generate_city_dict.py --countries ES PT FR IT DE GB
    python tools/generate_city_dict.py --min-pop 500 --countries ES PT FR IT DE
"""
from __future__ import annotations

import argparse
import io
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Optional
import urllib.request

# ── Configuración ─────────────────────────────────────────────────────────────

# Países a incluir (códigos ISO-3166 de GeoNames)
DEFAULT_COUNTRIES = ["ES", "PT", "FR", "IT", "DE", "GB", "AT", "CH", "BE",
                     "NL", "PL", "CZ", "HU", "HR", "GR", "TR", "MA", "US",
                     "MX", "AR", "BR", "CL", "PE", "CO", "JP", "CN", "TH",
                     "ID", "AU", "ZA", "AE", "EG", "IL", "IN", "VN", "SG",
                     "NZ", "IS", "IE", "SE", "NO", "DK", "FI", "RU", "UA",
                     "RO", "BG", "RS", "BA", "SI", "SK", "LT", "LV", "EE",
                     "MT", "CY", "LU", "MC", "AD", "SM", "VA", "ME", "MK",
                     "AL", "TN", "DZ", "LY", "KE", "TZ", "SN", "CM", "NG",
                     "CA", "CU", "DO", "JM", "CR", "PA", "GT", "HN", "SV",
                     "NI", "EC", "BO", "UY", "PY", "VE", "KR", "PH", "MY",
                     "MM", "NP", "LK", "BD", "PK", "AF", "UZ", "KZ", "GE",
                     "AM", "AZ", "JO", "LB", "SA", "IQ", "IR", "QA", "KW",
                     "BH", "OM", "YE", "MV", "NZ"]

# Nombres de países para comentarios en el fichero generado
COUNTRY_NAMES = {
    "ES": "España",         "PT": "Portugal",       "FR": "Francia",
    "IT": "Italia",         "DE": "Alemania",        "GB": "Reino Unido",
    "AT": "Austria",        "CH": "Suiza",           "BE": "Bélgica",
    "NL": "Países Bajos",   "PL": "Polonia",         "CZ": "Rep. Checa",
    "HU": "Hungría",        "HR": "Croacia",         "GR": "Grecia",
    "TR": "Turquía",        "MA": "Marruecos",       "US": "EEUU",
    "MX": "México",         "AR": "Argentina",       "BR": "Brasil",
    "CL": "Chile",          "PE": "Perú",            "CO": "Colombia",
    "JP": "Japón",          "CN": "China",           "TH": "Tailandia",
    "ID": "Indonesia",      "AU": "Australia",       "ZA": "Sudáfrica",
    "AE": "Emiratos",       "EG": "Egipto",          "IL": "Israel",
    "IN": "India",          "VN": "Vietnam",         "SG": "Singapur",
    "NZ": "Nueva Zelanda",  "IS": "Islandia",        "IE": "Irlanda",
    "SE": "Suecia",         "NO": "Noruega",         "DK": "Dinamarca",
    "FI": "Finlandia",      "RU": "Rusia",           "UA": "Ucrania",
    "RO": "Rumanía",        "BG": "Bulgaria",        "RS": "Serbia",
    "BA": "Bosnia",         "SI": "Eslovenia",       "SK": "Eslovaquia",
    "LT": "Lituania",       "LV": "Letonia",         "EE": "Estonia",
    "MT": "Malta",          "CY": "Chipre",          "LU": "Luxemburgo",
    "MC": "Mónaco",         "AD": "Andorra",         "SM": "San Marino",
    "VA": "Vaticano",       "ME": "Montenegro",      "MK": "Macedonia",
    "AL": "Albania",        "TN": "Túnez",           "DZ": "Argelia",
    "LY": "Libia",          "KE": "Kenia",           "TZ": "Tanzania",
    "SN": "Senegal",        "CM": "Camerún",         "NG": "Nigeria",
    "CA": "Canadá",         "CU": "Cuba",            "DO": "Rep. Dominicana",
    "JM": "Jamaica",        "CR": "Costa Rica",      "PA": "Panamá",
    "GT": "Guatemala",      "HN": "Honduras",        "SV": "El Salvador",
    "NI": "Nicaragua",      "EC": "Ecuador",         "BO": "Bolivia",
    "UY": "Uruguay",        "PY": "Paraguay",        "VE": "Venezuela",
    "KR": "Corea del Sur",  "PH": "Filipinas",       "MY": "Malasia",
    "MM": "Myanmar",        "NP": "Nepal",           "LK": "Sri Lanka",
    "BD": "Bangladesh",     "PK": "Pakistán",        "SA": "Arabia Saudí",
    "JO": "Jordania",       "LB": "Líbano",          "IQ": "Iraq",
    "IR": "Irán",           "QA": "Qatar",           "KW": "Kuwait",
    "BH": "Bahréin",        "OM": "Omán",            "MV": "Maldivas",
}

GEONAMES_URL = "https://download.geonames.org/export/dump/{code}.zip"
CACHE_DIR    = Path(__file__).parent / "_geonames_cache"

# Columnas del fichero GeoNames
COL_NAME        = 1
COL_ASCII       = 2
COL_ALTNAMES    = 3
COL_FEAT_CLASS  = 6
COL_FEAT_CODE   = 7
COL_COUNTRY     = 8
COL_POPULATION  = 14

# Solo lugares poblados
VALID_FEAT_CLASS = "P"


# ── Utilidades ────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Convierte a minúsculas y elimina acentos."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slug(text: str) -> str:
    """Convierte nombre a slug válido para carpetas (sin espacios ni caracteres raros)."""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s-]+", "_", s.strip())
    return s


def name_variants(name: str, ascii_name: str, alt_names: list[str]) -> set[str]:
    """Genera todas las variantes de búsqueda para un nombre de ciudad."""
    variants = set()
    for n in [name, ascii_name] + alt_names:
        n = n.strip()
        if not n or len(n) < 2:
            continue
        variants.add(n.lower())
        variants.add(normalize(n))
    return variants


def download_country(code: str) -> Optional[Path]:
    """Descarga y cachea el fichero de un país. Devuelve la ruta al .txt descomprimido."""
    CACHE_DIR.mkdir(exist_ok=True)
    txt_path = CACHE_DIR / f"{code}.txt"
    if txt_path.exists():
        return txt_path

    url = GEONAMES_URL.format(code=code)
    print(f"  Descargando {code} desde GeoNames...", end=" ", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            inner = f"{code}.txt"
            if inner not in zf.namelist():
                inner = zf.namelist()[0]
            txt_path.write_bytes(zf.read(inner))
        print("OK")
        return txt_path
    except Exception as e:
        print(f"ERROR ({e})")
        return None


def parse_country(txt_path: Path, min_pop: int) -> dict[str, str]:
    """
    Parsea el fichero GeoNames de un país y devuelve
    {keyword_minusculas: NombreSlug} para ciudades con población >= min_pop.
    """
    entries: dict[str, str] = {}

    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 15:
                continue
            if parts[COL_FEAT_CLASS] != VALID_FEAT_CLASS:
                continue
            try:
                pop = int(parts[COL_POPULATION])
            except ValueError:
                pop = 0
            if pop < min_pop:
                continue

            name       = parts[COL_NAME]
            ascii_name = parts[COL_ASCII]
            alt_raw    = parts[COL_ALTNAMES]
            alt_names  = [a for a in alt_raw.split(",") if a.strip()] if alt_raw else []

            dest_slug = slug(name)
            if not dest_slug:
                continue

            for variant in name_variants(name, ascii_name, alt_names):
                if len(variant) >= 2:
                    entries[variant] = dest_slug

    return entries


# ── Generación del fichero ────────────────────────────────────────────────────

# Código de la función matcher que se emite en el geocoder.py generado.
# Coincidencia por palabra completa (no subcadena) para evitar falsos positivos.
_MATCHER_CODE = '''
import re as _re2
import unicodedata as _ud

_MATCH_MIN_LEN = 4

_STOPWORDS = {
    "foto", "fotos", "photo", "photos", "image", "images", "img", "imagen",
    "imagenes", "video", "videos", "dcim", "piso", "casa", "hogar", "varios",
    "otros", "nuevo", "nueva", "copia", "backup", "movil", "camara", "camera",
    "whatsapp", "screenshot", "captura", "descargas", "download", "downloads",
    "documentos", "documents", "escritorio", "desktop", "takeout", "google",
}

_single_index = None
_multi_index = None


def _norm_text(s):
    nfkd = _ud.normalize("NFKD", s.lower())
    return "".join(c for c in nfkd if not _ud.combining(c))


def _build_index():
    global _single_index, _multi_index
    _single_index = {}
    _multi_index = {}
    for kw, city in FOLDER_CITY_KEYWORDS.items():
        words = [w for w in _re2.split(r"[^a-z0-9]+", _norm_text(kw)) if w]
        if not words:
            continue
        phrase = " ".join(words)
        if len(phrase) < _MATCH_MIN_LEN:
            continue
        if len(words) == 1:
            if words[0] in _STOPWORDS:
                continue
            _single_index.setdefault(words[0], city)
        else:
            _multi_index.setdefault(words[0], []).append((tuple(words), city))


def city_from_folder_name(folder_name):
    """Detecta una ciudad por coincidencia de palabra completa."""
    if _single_index is None:
        _build_index()
    tokens = [t for t in _re2.split(r"[^a-z0-9]+", _norm_text(folder_name)) if t]
    if not tokens:
        return None
    for i, tok in enumerate(tokens):
        cands = _multi_index.get(tok)
        if cands:
            for words, city in cands:
                n = len(words)
                if tuple(tokens[i:i + n]) == words:
                    return city
    for tok in tokens:
        city = _single_index.get(tok)
        if city:
            return city
    return None
'''


def generate(countries: list[str], min_pop: int, output_path: Path):
    all_entries: dict[str, dict[str, str]] = {}  # country → {keyword: slug}

    for code in countries:
        txt = download_country(code)
        if txt is None:
            continue
        entries = parse_country(txt, min_pop)
        all_entries[code] = entries
        total = len(set(entries.values()))
        print(f"  {code}: {total} ciudades, {len(entries)} keywords")

    # ── Escribir geocoder.py ───────────────────────────────────────────────
    lines = []
    lines.append('"""Geocodificación inversa: coordenadas GPS → ciudad/país (sin internet)."""')
    lines.append("from __future__ import annotations\n")
    lines.append("from functools import lru_cache")
    lines.append("from typing import Optional\n")
    lines.append("_rg = None\n")
    lines.append("def _get_rg():")
    lines.append("    global _rg")
    lines.append("    if _rg is None:")
    lines.append("        import reverse_geocoder as rg")
    lines.append("        _rg = rg")
    lines.append("    return _rg\n")
    lines.append("")
    lines.append("@lru_cache(maxsize=4096)")
    lines.append("def coords_to_city(lat: float, lon: float) -> Optional[str]:")
    lines.append('    """Devuelve el nombre de la ciudad más cercana. Usa caché."""')
    lines.append("    try:")
    lines.append("        rg = _get_rg()")
    lines.append("        results = rg.search([(lat, lon)], verbose=False)")
    lines.append("        if results:")
    lines.append('            city = results[0].get("name", "").strip()')
    lines.append("            return city if city else None")
    lines.append("    except Exception:")
    lines.append("        pass")
    lines.append("    return None\n")
    lines.append("")
    lines.append("# Generado automáticamente por tools/generate_city_dict.py")
    total_keywords = sum(len(v) for v in all_entries.values())
    total_cities   = sum(len(set(v.values())) for v in all_entries.values())
    lines.append(f"# {total_cities} ciudades — {total_keywords} keywords — población mínima: {min_pop}")
    lines.append("FOLDER_CITY_KEYWORDS: dict[str, str] = {")

    for code in countries:
        if code not in all_entries or not all_entries[code]:
            continue
        country_name = COUNTRY_NAMES.get(code, code)
        lines.append(f"\n    # {'═' * 60}")
        lines.append(f"    # {country_name} ({code})")
        lines.append(f"    # {'═' * 60}")
        for kw, dest in sorted(all_entries[code].items(), key=lambda x: x[1]):
            kw_escaped   = kw.replace("\\", "\\\\").replace('"', '\\"')
            dest_escaped = dest.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'    "{kw_escaped}": "{dest_escaped}",')

    lines.append("}\n")
    lines.append("")
    lines.append(_MATCHER_CODE)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Fichero generado: {output_path}")
    print(f"  Total ciudades  : {total_cities}")
    print(f"  Total keywords  : {total_keywords}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Genera el diccionario de ciudades en core/geocoder.py desde GeoNames."
    )
    parser.add_argument(
        "--min-pop", type=int, default=5000,
        help="Población mínima para incluir una ciudad (default: 5000)"
    )
    parser.add_argument(
        "--countries", nargs="+", default=DEFAULT_COUNTRIES,
        help="Códigos ISO de países a incluir (default: lista completa)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Ruta de salida (default: core/geocoder.py)"
    )
    args = parser.parse_args()

    output = Path(args.output) if args.output else Path(__file__).parent.parent / "core" / "geocoder.py"

    print(f"\nGenerando diccionario de ciudades")
    print(f"  Países     : {len(args.countries)}")
    print(f"  Población mínima: {args.min_pop:,}")
    print(f"  Salida     : {output}\n")

    generate(args.countries, args.min_pop, output)
    print("\nListo. Ejecuta 'git diff core/geocoder.py' para revisar los cambios.")


if __name__ == "__main__":
    main()
