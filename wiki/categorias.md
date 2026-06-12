# Categorías (lista cerrada)

El sistema produce **únicamente** estas 11 categorías. Cualquier clasificación
que no encaje en la lista se reconduce automáticamente a `Sin_clasificar`,
de modo que nunca aparecen carpetas inesperadas.

La lista está definida en un único sitio: [`core/categories.py`](../core/categories.py).

| Categoría | Qué contiene | Subcarpeta |
|-----------|--------------|------------|
| `Personas` | Personas como elemento dominante | — |
| `Familia` | Fotos familiares (por nombre de carpeta) | — |
| `Eventos` | Bodas, cumpleaños, fiestas... agrupados por fecha | `Evento_NN` |
| `Viajes` | Personas en exterior con ubicación conocida | `<ciudad>` |
| `Ciudades` | Escenas urbanas y monumentos | `<ciudad>` o `Sin_ubicacion` |
| `Naturaleza` | Paisajes sin personas ni ciudad | — |
| `Animales` | Mascotas y animales en primer plano | — |
| `Hogar` | Interiores sin personas (habitaciones, mobiliario) | — |
| `Comida` | Platos y comida en primer plano | — |
| `Documentos` | Papeles, capturas, carteles con texto | — |
| `Sin_clasificar` | Todo lo que no se reconoce con confianza | — |

## Cómo se decide la categoría (modo `--two-step`)

```
Documentos / Comida / Animales   → primeros planos (máxima prioridad)
Monumento o escena urbana        → Ciudades/<ciudad>
Persona dominante + exterior+GPS → Viajes/<ciudad>
Persona dominante                → Personas
Paisaje natural                  → Naturaleza
Interior sin personas            → Hogar
Con ciudad pero sin tema claro   → Ciudades/<ciudad>
Nada reconocible                 → Sin_clasificar
```

Las categorías por **nombre de carpeta origen** (Viajes, Eventos, Familia...)
tienen prioridad sobre la clasificación visual.

## Cambiar la lista

Para añadir o quitar una categoría hay que tocar `core/categories.py`
(el conjunto `CANONICAL_CATEGORIES`) y, si es una categoría visual nueva,
añadir sus prompts en `core/detector.py` (`CONTEXT_PROMPTS`).
