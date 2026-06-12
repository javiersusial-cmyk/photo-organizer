"""Geocodificación inversa: coordenadas GPS → ciudad/país (sin internet)."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

_rg = None


def _get_rg():
    global _rg
    if _rg is None:
        import reverse_geocoder as rg
        _rg = rg
    return _rg


@lru_cache(maxsize=4096)
def coords_to_city(lat: float, lon: float) -> Optional[str]:
    """
    Devuelve el nombre de la ciudad más cercana a las coordenadas dadas.
    Usa caché para no recalcular coordenadas repetidas.
    """
    try:
        rg = _get_rg()
        results = rg.search([(lat, lon)], verbose=False)
        if results:
            r = results[0]
            city = r.get("name", "").strip()
            return city if city else None
    except Exception:
        pass
    return None


# Palabras clave en nombres de carpeta → ciudades/destinos conocidos
# Añade aquí los nombres que aparezcan en tus carpetas
FOLDER_CITY_KEYWORDS: dict[str, str] = {
    "paris":      "Paris",
    "roma":       "Roma",
    "rome":       "Roma",
    "madrid":     "Madrid",
    "barcelona":  "Barcelona",
    "london":     "Londres",
    "londres":    "Londres",
    "new york":   "Nueva_York",
    "nueva york": "Nueva_York",
    "newyork":    "Nueva_York",
    "amsterdam":  "Amsterdam",
    "berlin":     "Berlin",
    "lisboa":     "Lisboa",
    "lisbon":     "Lisboa",
    "tokyo":      "Tokyo",
    "tokio":      "Tokyo",
    "dubai":      "Dubai",
    "mexico":     "Mexico",
    "cancun":     "Cancun",
    "miami":      "Miami",
    "venice":     "Venecia",
    "venecia":    "Venecia",
    "florencia":  "Florencia",
    "florence":   "Florencia",
    "prague":     "Praga",
    "praga":      "Praga",
    "vienna":     "Viena",
    "viena":      "Viena",
    "budapest":   "Budapest",
    "athens":     "Atenas",
    "atenas":     "Atenas",
    "cairo":      "El_Cairo",
    "marrakech":  "Marrakech",
    "bangkok":    "Bangkok",
    "bali":       "Bali",
    "sydney":     "Sydney",
    "toronto":    "Toronto",
    "chicago":    "Chicago",
    "tenerife":   "Tenerife",
    "mallorca":   "Mallorca",
    "ibiza":      "Ibiza",
    "lanzarote":  "Lanzarote",
    "sevilla":    "Sevilla",
    "granada":    "Granada",
    "toledo":     "Toledo",
    "bilbao":     "Bilbao",
    "valencia":   "Valencia",
    "zaragoza":   "Zaragoza",
}


def city_from_folder_name(folder_name: str) -> Optional[str]:
    """Detecta una ciudad conocida en el nombre de la carpeta."""
    lower = folder_name.lower()
    for keyword, city in FOLDER_CITY_KEYWORDS.items():
        if keyword in lower:
            return city
    return None
