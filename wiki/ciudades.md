# Añadir nuevas ciudades

El sistema detecta ciudades de dos formas distintas. Puedes ampliar ambas.

## 1. Desde el nombre de la carpeta origen

Edita el diccionario `FOLDER_CITY_KEYWORDS` en `core/geocoder.py`:

```python
FOLDER_CITY_KEYWORDS: dict[str, str] = {
    "donostia":      "Donostia",
    "san sebastian": "Donostia",
    "mi ciudad":     "Mi_Ciudad",   # ← añade aquí
    ...
}
```

- La **clave** es lo que puede aparecer en el nombre de la carpeta (en minúsculas)
- El **valor** es el nombre de la subcarpeta que se creará en destino
- Puedes tener varias claves para el mismo destino (alias, idiomas, faltas de ortografía)

## 2. Desde coordenadas GPS

La geocodificación GPS usa la base de datos offline de `reverse_geocoder`, que cubre todo el mundo a nivel de ciudad. No necesitas configuración adicional — si la foto tiene GPS, la ciudad se detecta automáticamente.

Si `reverse_geocoder` devuelve un nombre que no te gusta (ej: "San Sebastián" en lugar de "Donostia"), puedes añadir una normalización en `core/geocoder.py`:

```python
GPS_CITY_NORMALIZE: dict[str, str] = {
    "San Sebastián": "Donostia",
    "San Sebastian": "Donostia",
    "Bilbo":         "Bilbao",
}
```

Y en la función `coords_to_city`:

```python
city = r.get("name", "").strip()
city = GPS_CITY_NORMALIZE.get(city, city)  # normalizar
```

## Ciudades ya incluidas

El diccionario incluye más de 100 ciudades españolas organizadas por región:

- **País Vasco**: Donostia, Bilbao, Vitoria, Hondarribia, Zarautz, Getaria, Zumaia, Lekeitio, Bermeo, Guernica, Mundaka, Irun, Renteria...
- **Cataluña**: Barcelona, Girona, Tarragona, Lleida, Sitges, Cadaqués, Montserrat...
- **Andalucía**: Sevilla, Granada, Málaga, Córdoba, Cádiz, Marbella, Ronda, Nerja...
- **Comunidad Valenciana**: Valencia, Alicante, Benidorm, Dénia, Jávea, Peñíscola...
- **Galicia**: Santiago de Compostela, Vigo, A Coruña, Pontevedra...
- **Castilla**: Madrid, Toledo, Segovia, Ávila, Salamanca, Burgos, León...
- **Asturias/Cantabria**: Oviedo, Gijón, Santander, Comillas, Picos de Europa...
- **Islas**: Mallorca, Menorca, Ibiza, Formentera, Tenerife, Gran Canaria, Lanzarote, Fuerteventura...
- **Europa**: París, Roma, Londres, Amsterdam, Berlín, Lisboa, Praga, Viena, Budapest, Atenas...
- **Resto del mundo**: Tokyo, Dubai, México, Cancún, Miami, Bangkok, Bali, Sydney...
