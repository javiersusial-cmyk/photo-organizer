# Cómo funciona la clasificación

El sistema combina tres fuentes de información con esta prioridad:

```
1º Nombre de la carpeta origen   (máxima confianza)
2º Coordenadas GPS de la foto
3º Modelo CLIP (inteligencia artificial)
4º Sin_clasificar (fallback)
```

## 1. Nombre de la carpeta origen

Si tus fotos ya están en carpetas con nombres descriptivos, el programa los respeta:

| Carpeta origen | Resultado |
|----------------|-----------|
| `2019_Viaje_Roma/` | `2019/Viajes/Roma/` |
| `Boda_Maria_2021/` | `2021/Eventos/Evento_01/` |
| `Navidad_2020/` | `2020/Eventos/Evento_01/` |
| `Vacaciones_Paris_2018/` | `2018/Viajes/Paris/` |
| `2023/` | `2023/` (solo el año) |

Reconoce años (4 dígitos), ciudades (ver [ciudades.md](ciudades.md)) y palabras clave de categorías.

## 2. GPS → Ciudad

Si la foto tiene coordenadas GPS (la mayoría de las tomadas con móvil desde ~2008):

- Se hace geocodificación inversa **offline** con `reverse_geocoder`
- La ciudad más cercana se usa como subcarpeta de Viajes
- Resultado: `2022/Viajes/Donostia/`

## 3. Modelo CLIP

CLIP es un modelo de IA de OpenAI que compara imágenes con descripciones de texto. Para cada foto, compara la imagen contra todas las frases definidas en `config.yaml` y asigna la categoría con mayor similitud.

- Umbral mínimo de confianza: 0.20 (configurable en `classifier.py`)
- Por debajo del umbral → `Sin_clasificar`
- Solo se usa cuando ni el nombre de carpeta ni el GPS dan información

## 4. Agrupación de Eventos

Las fotos clasificadas como `Eventos` se subdividen automáticamente:

- Se ordenan por fecha de toma
- Si hay una brecha mayor a N horas entre fotos consecutivas → nuevo evento
- Resultado: `Eventos/Evento_01/`, `Eventos/Evento_02/`, ...

Esto permite identificar bodas, cumpleaños, fiestas... aunque no sepas el nombre del evento.
