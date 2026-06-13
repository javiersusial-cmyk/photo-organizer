"""
Lista cerrada y única de categorías del sistema.

Todo el programa debe producir SOLO estas categorías base. Cualquier
otra cosa se reconduce a 'Sin_clasificar'. Esto evita que aparezcan
carpetas inesperadas.

Algunas categorías llevan subcarpeta tras una barra:
  Viajes/<ciudad>      Ciudades/<ciudad>     Eventos/Evento_NN
"""
from __future__ import annotations

# Conjunto cerrado de categorías base permitidas
CANONICAL_CATEGORIES: set[str] = {
    "Personas",
    "Familia",
    "Eventos",
    "Viajes",
    "Ciudad",
    "Naturaleza",
    "Animales",
    "Hogar",
    "Comida",
    "Documentos",
    "Sin_clasificar",
}


def canonical(category: str, fallback: str = "Sin_clasificar") -> str:
    """
    Valida una categoría (posiblemente con subcarpeta 'Cat/Sub') contra la
    lista cerrada. Si la base no está permitida, devuelve el fallback.
    """
    if not category:
        return fallback
    base = category.split("/", 1)[0]
    if base in CANONICAL_CATEGORIES:
        return category
    return fallback
