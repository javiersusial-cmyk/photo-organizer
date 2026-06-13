# Consolidador de fotos (consolidate.py)

Motor principal del proyecto (v2). Reorganiza una colección anárquica de fotos
**conservando los nombres de carpeta que ya tienen sentido** (viajes, ciudades,
eventos) y completándolos con el año, en lugar de reclasificar todo con IA.

## Filosofía

| Situación en origen | Qué hace |
|---------------------|----------|
| Carpeta con sentido (`Viajes/2011 Venecia-Paris`, `Ciudades/Bilbao`...) | Conserva el nombre, deduce el tipo y asigna el año → `Año YYYY / Tipo - Nombre (fecha)` |
| Volcado sin contexto (`Camaras/Fotos Pentax`, fechas sueltas) | Agrupa por **sesiones de fecha/hora** → `Año YYYY / Sin clasificar / 2007-06-14` |
| Sesión de menos de 5 fotos o sin fecha | Va a `Sin clasificar / resto` |
| IA (opcional, `--ai`) | **Última capa**: solo sobre el "resto", reparte en Personas/Naturaleza/Ciudades (+monumentos) |
| Duplicado exacto (mismo nombre + metadatos) | Se copia a `Duplicadas/Año YYYY/` para revisión (no se pierde nada) |

## Estructura de salida

```
C:\Fotos catalogadas\
├── Año 2005\
│   ├── Viaje - Tanzania (2005 Noviembre)\
│   ├── Ciudad - Bilbao (2005)\
│   ├── Evento - Boda Javi y Maria (20051112)\
│   └── Sin clasificar\
│       ├── 2005-07-07\
│       └── resto\
├── Google fotos\           ← solo fotos de Google que no existían
│   └── Año 2016\...
├── Duplicadas\             ← copias detectadas, para revisar
│   └── Año 2007\
├── catalogo.db             ← catálogo único (dedup entre ejecuciones)
├── preview_dryrun.csv      ← plan de la última previsualización
└── errores.csv             ← incidencias de lectura
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--source` | Carpeta origen (obligatorio) |
| `--dest` | Carpeta destino — debe ser **siempre la misma** (ahí vive `catalogo.db`) |
| `--dry-run` | Previsualiza sin copiar ni tocar el catálogo |
| `--ai` | Activa la IA como última capa sobre el "resto" |
| `--landmark-threshold` | Sensibilidad de monumentos (default 0.30; más alto = menos falsos positivos) |
| `--session-gap` | Horas de separación para una nueva sesión (default 12) |
| `--google` | Fase Google: las nuevas van a `Google fotos/` |
| `--skip-existing` | No copia fotos cuyo nombre ya exista en CUALQUIER carpeta del destino |
| `--catalog` | Ruta alternativa del catálogo (default `DEST/catalogo.db`) |

## El catálogo (catalogo.db)

- Es un **único fichero SQLite** en el destino, memoria de deduplicación entre ejecuciones.
- **El `--dry-run` NO escribe en el catálogo**: solo genera el CSV de preview.
- Solo la **ejecución real** llena el catálogo.
- En ejecuciones reales posteriores, el catálogo evita recopiar lo ya colocado.

## Duplicados

- Duplicado = **mismo nombre + mismos metadatos** (tamaño, fecha, dimensiones). No es perceptual (no afecta el brillo/recorte).
- La primera copia se coloca; las siguientes van a `Duplicadas/Año YYYY/` para que las revises.
- El origen **nunca se borra** (se copia, no se mueve).

---

# Flujo recomendado paso a paso

> **Importante:** la colección principal debe hacerse **real antes** de previsualizar
> Google, porque `--skip-existing` compara contra las fotos que ya hay en el destino.

Sustituye las rutas por las tuyas. Destino fijo: `C:\Fotos catalogadas`.

### 1. Preview de la colección principal (sin Google)

```powershell
cd "C:\Users\javie\OneDrive\Desarrollo\photo-organizer"

python consolidate.py --source "C:\Users\javie\Documents\Documentos PC sobremesa\Fotos no normalizadas\Fotos mias" --dest "C:\Fotos catalogadas" --dry-run
```

Revisa `C:\Fotos catalogadas\preview_dryrun.csv` (ciérralo en Excel antes de relanzar).
Consulta dónde va una foto concreta:

```powershell
python buscar.py --dest "C:\Fotos catalogadas" _IGP1032.DNG
```

### 2. Ejecución REAL de la principal

```powershell
python consolidate.py --source "C:\Users\javie\Documents\Documentos PC sobremesa\Fotos no normalizadas\Fotos mias" --dest "C:\Fotos catalogadas"
```

Esto copia las fotos y llena `catalogo.db`.

### 3. Preview de Google (ya ve lo que hay en el destino)

```powershell
python consolidate.py --source "C:\Users\javie\Documents\Documentos PC sobremesa\Fotos no normalizadas\Fotos Google photos 210331" --dest "C:\Fotos catalogadas" --google --skip-existing --dry-run

python consolidate.py --source "C:\Users\javie\Documents\Documentos PC sobremesa\Fotos no normalizadas\Google 201115" --dest "C:\Fotos catalogadas" --google --skip-existing --dry-run
```

El resumen indica `Ya existían en el destino (omitidas): N` y cuántas son nuevas.

### 4. Ejecución REAL de Google

```powershell
python consolidate.py --source "...\Fotos Google photos 210331" --dest "C:\Fotos catalogadas" --google --skip-existing

python consolidate.py --source "...\Google 201115" --dest "C:\Fotos catalogadas" --google --skip-existing
```

Solo las fotos de Google que no existían en ningún sitio se copian a `Google fotos/`.

---

## Notas

- Añade `--ai` en cualquier paso si quieres que la IA reparta el "resto".
- El origen no se modifica nunca; puedes borrar manualmente al final tras revisar.
- Incidencias de lectura (ficheros no legibles, RAW sin miniatura) en `errores.csv`.
