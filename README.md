# 📷 Photo Organizer

Herramienta en Python para organizar, deduplicar y catalogar colecciones grandes de fotos (decenas de miles de imágenes), ejecutándose en local.

El método principal es el **consolidador** (`consolidate.py`): respeta tu organización manual, agrupa lo suelto por fecha y mantiene un catálogo único para no duplicar nada entre ejecuciones.

---

## Cómo organiza las fotos

| Situación en origen | Resultado |
|---------------------|-----------|
| Carpeta con sentido (`Viajes/2011 Venecia-Paris`, `Ciudades/Bilbao`, `Boda...`) | Conserva el nombre, deduce el tipo y asigna el año → `Año YYYY / Tipo - Nombre (fecha)` |
| Volcado sin contexto (`Camaras/Fotos Pentax`, fechas sueltas) | Agrupa por **sesiones de fecha/hora** → `Año YYYY / Sin clasificar / 2007-06-14` |
| Sesión de menos de 5 fotos o sin fecha | `Sin clasificar / resto` |
| IA opcional (`--ai`, última capa) | Solo sobre el "resto": reparte en Personas / Naturaleza / Ciudades (+monumentos) |
| Duplicado exacto (mismo nombre + metadatos) | Se copia a `Duplicadas/` para revisión (nunca se pierde nada) |

### Estructura de salida

```
C:\Fotos catalogadas\
├── Año 2005\
│   ├── Viaje - Tanzania (2005 Noviembre)\
│   ├── Ciudad - Bilbao (2005)\
│   ├── Evento - Boda Javi y Maria (20051112)\
│   └── Sin clasificar\
│       ├── 2005-07-07\
│       └── resto\
├── Google fotos\        ← solo fotos de Google que no existían en el destino
├── Duplicadas\          ← copias detectadas, para revisar antes de borrar
├── catalogo.db          ← catálogo único (deduplicación entre ejecuciones)
├── preview_dryrun.csv   ← plan de la última previsualización
└── errores.csv          ← incidencias de lectura (ficheros dañados, etc.)
```

---

## Instalación

```powershell
git clone https://github.com/javiersusial-cmyk/photo-organizer.git
cd photo-organizer

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

> La IA (`--ai`) descarga modelos (~1.5 GB CLIP + 6 MB YOLO) la primera vez. Si no usas `--ai`, no hacen falta.

---

## Flujo recomendado (paso a paso)

Mantén **siempre el mismo `--dest`**: ahí vive `catalogo.db`, que evita duplicar entre pasadas.

> **Importante:** la colección principal se hace **real antes** de previsualizar Google,
> porque `--skip-existing` compara contra las fotos que ya hay en el destino.

### 1. Preview de la colección principal (rápido, no copia nada)

```powershell
python consolidate.py --source "C:\...\Fotos mias" --dest "C:\Fotos catalogadas" --dry-run
```

Revisa el plan en `C:\Fotos catalogadas\preview_dryrun.csv` (ciérralo en Excel antes de relanzar).

### 2. Ejecución REAL de la principal (copia y llena el catálogo)

```powershell
python consolidate.py --source "C:\...\Fotos mias" --dest "C:\Fotos catalogadas"
```

### 3. Preview de Google (ya ve lo que hay en el destino)

```powershell
python consolidate.py --source "C:\...\Fotos Google photos 210331" --dest "C:\Fotos catalogadas" --google --skip-existing --dry-run
```

### 4. Ejecución REAL de Google

```powershell
python consolidate.py --source "C:\...\Fotos Google photos 210331" --dest "C:\Fotos catalogadas" --google --skip-existing
```

Solo las fotos de Google que **no existían** en ningún sitio del destino se copian a `Google fotos/`.

---

## Comprobar dónde va una foto

Antes o después de copiar, consulta el destino de cualquier foto por nombre (o parte):

```powershell
# Por nombre exacto
python buscar.py --dest "C:\Fotos catalogadas" _IGP1032.DNG

# Por parte del nombre
python buscar.py --dest "C:\Fotos catalogadas" IMGP0334

# Por carpeta/lugar
python buscar.py --dest "C:\Fotos catalogadas" sudafrica
```

Muestra, para cada coincidencia, el **origen**, el **destino** y la **vía** (`Carpeta`, `IA`, `Duplicada`). Busca tanto en el preview (plan) como en el catálogo (lo ya colocado).

---

## Opciones de `consolidate.py`

| Opción | Descripción |
|--------|-------------|
| `--source` | Carpeta origen (obligatorio) |
| `--dest` | Carpeta destino — siempre la misma (contiene `catalogo.db`) |
| `--dry-run` | Previsualiza sin copiar ni tocar el catálogo |
| `--ai` | IA como última capa sobre el "resto" |
| `--landmark-threshold` | Sensibilidad de monumentos (default 0.30) |
| `--session-gap` | Horas para una nueva sesión (default 12) |
| `--google` | Fase Google: las nuevas van a `Google fotos/` |
| `--skip-existing` | No copia fotos cuyo nombre ya exista en cualquier carpeta del destino |
| `--catalog` | Ruta alternativa del catálogo |

---

## Garantías

- **El origen nunca se toca** (se copia, no se mueve). Borra tú al final, tras revisar.
- **Nada se pierde**: los duplicados van a `Duplicadas/` y los ficheros ilegibles quedan listados en `errores.csv`.
- **Multi-paso seguro**: el catálogo recuerda lo ya colocado; puedes parar y reanudar.
- **El `--dry-run` no modifica el catálogo**: previsualiza cuanto quieras.

---

## Documentación

- **[Consolidador — guía completa y flujo](wiki/consolidador.md)** ⭐
- [Categorías (lista cerrada)](wiki/categorias.md)
- [Solución de problemas](wiki/troubleshooting.md)

### Enfoque anterior (`run.py`)

El `run.py` original hace una clasificación 100% por IA (CLIP/YOLO) con inventario Excel, geocodificación GPS y checkpoint. Sigue disponible pero el método recomendado es el consolidador. Su documentación: [clasificación](wiki/clasificacion.md), [clustering](wiki/clustering.md), [checkpoint](wiki/checkpoint.md), [ciudades](wiki/ciudades.md), [configuración](wiki/configuracion.md).

## Dependencias

Ver [requirements.txt](requirements.txt).
