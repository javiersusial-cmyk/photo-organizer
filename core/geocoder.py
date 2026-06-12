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
    # ── Islas españolas ──────────────────────────────────────────────────────
    "tenerife":       "Tenerife",
    "gran canaria":   "Gran_Canaria",
    "fuerteventura":  "Fuerteventura",
    "lanzarote":      "Lanzarote",
    "la palma":       "La_Palma",
    "la gomera":      "La_Gomera",
    "el hierro":      "El_Hierro",
    "mallorca":       "Mallorca",
    "palma":          "Mallorca",
    "menorca":        "Menorca",
    "ibiza":          "Ibiza",
    "formentera":     "Formentera",
    # ── País Vasco ───────────────────────────────────────────────────────────
    "donostia":       "Donostia",
    "san sebastian":  "Donostia",
    "san sebastián":  "Donostia",
    "bilbao":         "Bilbao",
    "vitoria":        "Vitoria",
    "gasteiz":        "Vitoria",
    "hondarribia":    "Hondarribia",
    "zarautz":        "Zarautz",
    "getaria":        "Getaria",
    "zumaia":         "Zumaia",
    "mutriku":        "Mutriku",
    "lekeitio":       "Lekeitio",
    "bermeo":         "Bermeo",
    "guernica":       "Guernica",
    "gernika":        "Guernica",
    "mundaka":        "Mundaka",
    "ondarroa":       "Ondarroa",
    "elgoibar":       "Elgoibar",
    "eibar":          "Eibar",
    "arrasate":       "Mondragon",
    "mondragon":      "Mondragon",
    "beasain":        "Beasain",
    "tolosa":         "Tolosa",
    "azpeitia":       "Azpeitia",
    "zumarraga":      "Zumarraga",
    "irun":           "Irun",
    "renteria":       "Renteria",
    "errenteria":     "Renteria",
    "pasajes":        "Pasajes",
    "pasaia":         "Pasajes",
    "andoain":        "Andoain",
    "hernani":        "Hernani",
    "biarritz":       "Biarritz",
    # ── Navarra / La Rioja ───────────────────────────────────────────────────
    "pamplona":       "Pamplona",
    "iruña":          "Pamplona",
    "logrono":        "Logrono",
    "logroño":        "Logrono",
    "estella":        "Estella",
    "tudela":         "Tudela",
    # ── Aragón ───────────────────────────────────────────────────────────────
    "zaragoza":       "Zaragoza",
    "huesca":         "Huesca",
    "teruel":         "Teruel",
    "jaca":           "Jaca",
    "benasque":       "Benasque",
    "ordesa":         "Ordesa",
    # ── Cataluña ─────────────────────────────────────────────────────────────
    "barcelona":      "Barcelona",
    "girona":         "Girona",
    "gerona":         "Girona",
    "tarragona":      "Tarragona",
    "lleida":         "Lleida",
    "lerida":         "Lleida",
    "sitges":         "Sitges",
    "costa brava":    "Costa_Brava",
    "cadaques":       "Cadaques",
    "cadaqués":       "Cadaques",
    "figueres":       "Figueres",
    "vic":            "Vic",
    "manresa":        "Manresa",
    "montserrat":     "Montserrat",
    # ── Comunidad Valenciana ─────────────────────────────────────────────────
    "valencia":       "Valencia",
    "alicante":       "Alicante",
    "benidorm":       "Benidorm",
    "denia":          "Denia",
    "javea":          "Javea",
    "jávea":          "Javea",
    "calpe":          "Calpe",
    "altea":          "Altea",
    "gandia":         "Gandia",
    "castellon":      "Castellon",
    "castellón":      "Castellon",
    "peniscola":      "Peniscola",
    "peñíscola":      "Peniscola",
    # ── Andalucía ────────────────────────────────────────────────────────────
    "sevilla":        "Sevilla",
    "granada":        "Granada",
    "malaga":         "Malaga",
    "málaga":         "Malaga",
    "cordoba":        "Cordoba",
    "córdoba":        "Cordoba",
    "cadiz":          "Cadiz",
    "cádiz":          "Cadiz",
    "huelva":         "Huelva",
    "almeria":        "Almeria",
    "almería":        "Almeria",
    "jaen":           "Jaen",
    "jaén":           "Jaen",
    "marbella":       "Marbella",
    "torremolinos":   "Torremolinos",
    "nerja":          "Nerja",
    "ronda":          "Ronda",
    "jerez":          "Jerez",
    "tarifa":         "Tarifa",
    "gibraltar":      "Gibraltar",
    # ── Castilla ─────────────────────────────────────────────────────────────
    "madrid":         "Madrid",
    "toledo":         "Toledo",
    "segovia":        "Segovia",
    "avila":          "Avila",
    "ávila":          "Avila",
    "salamanca":      "Salamanca",
    "valladolid":     "Valladolid",
    "burgos":         "Burgos",
    "leon":           "Leon",
    "león":           "Leon",
    "zamora":         "Zamora",
    "palencia":       "Palencia",
    "soria":          "Soria",
    "guadalajara":    "Guadalajara",
    "cuenca":         "Cuenca",
    "ciudad real":    "Ciudad_Real",
    "albacete":       "Albacete",
    # ── Galicia ──────────────────────────────────────────────────────────────
    "santiago":       "Santiago_de_Compostela",
    "compostela":     "Santiago_de_Compostela",
    "vigo":           "Vigo",
    "coruña":         "A_Coruna",
    "a coruña":       "A_Coruna",
    "pontevedra":     "Pontevedra",
    "ourense":        "Ourense",
    "lugo":           "Lugo",
    "rias bajas":     "Rias_Bajas",
    # ── Asturias / Cantabria ─────────────────────────────────────────────────
    "oviedo":         "Oviedo",
    "gijon":          "Gijon",
    "gijón":          "Gijon",
    "aviles":         "Aviles",
    "avilés":         "Aviles",
    "santander":      "Santander",
    "comillas":       "Comillas",
    "san vicente":    "San_Vicente_Barquera",
    "picos de europa":"Picos_de_Europa",
    "covadonga":      "Covadonga",
    # ── Extremadura / Murcia ─────────────────────────────────────────────────
    "caceres":        "Caceres",
    "cáceres":        "Caceres",
    "badajoz":        "Badajoz",
    "merida":         "Merida",
    "mérida":         "Merida",
    "murcia":         "Murcia",
    "cartagena":      "Cartagena",
    # ── Resto ciudades España ────────────────────────────────────────────────
    "elche":          "Elche",
    "elx":            "Elche",
    "alcala":         "Alcala_de_Henares",
    "aranjuez":       "Aranjuez",
    "el escorial":    "El_Escorial",
}


def city_from_folder_name(folder_name: str) -> Optional[str]:
    """Detecta una ciudad conocida en el nombre de la carpeta."""
    lower = folder_name.lower()
    for keyword, city in FOLDER_CITY_KEYWORDS.items():
        if keyword in lower:
            return city
    return None
