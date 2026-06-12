# 📷 Photo Organizer

Herramienta en Python para clasificar, desduplicar y organizar colecciones grandes de fotos (miles o decenas de miles de imágenes).

## ¿Qué hace?

1. **Escanea** carpetas y subcarpetas buscando imágenes
2. **Extrae metadatos EXIF** (fecha, cámara, coordenadas GPS)
3. **Detecta duplicados** mediante hash perceptual (imagehash)
4. **Clasifica temáticamente** con el modelo CLIP (IA local, sin internet)
5. **Geocodifica** coordenadas GPS a ciudad/país (offline, ~50 MB)
6. **Respeta estructura existente** — si tus carpetas ya tienen nombre de ciudad o año, los conserva
7. **Agrupa eventos** — fotos de la misma categoría separadas por más de N horas van a carpetas distintas (`Evento_01`, `Evento_02`...)
8. **Copia** las fotos organizadas a la carpeta destino (el original no se toca)
9. **Genera inventario** en CSV y Excel con todos los metadatos
10. **Checkpoint** — si el proceso se interrumpe, al relanzar continúa donde se quedó

## Estructura de salida

```
fotos_organizadas/
├── 2022/
│   ├── Viajes/
│   │   ├── Donostia/
│   │   ├── Paris/
│   │   └── Roma/
│   ├── Eventos/
│   │   ├── Evento_01/
│   │   └── Evento_02/
│   ├── Personas/
│   ├── Familia/
│   └── Sin_clasificar/
├── _Duplicados/
│   └── 2022/
├── mis_fotos_inventario.csv
└── mis_fotos_inventario.xlsx
```

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd photo-organizer

# Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Instalar dependencias
pip install -r requirements.txt
```

> **Nota:** La primera ejecución con clasificación CLIP descarga el modelo (~1.5 GB). Solo ocurre una vez.

## Uso

```bash
# Clasificación completa
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas"

# Sin clasificación CLIP (más rápido, usa solo GPS y nombres de carpeta)
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --no-classify

# Solo inventario, sin copiar ficheros
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --only-inventory

# Ajustar brecha entre eventos (default 12h)
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --event-gap 24

# Empezar desde cero (ignorar checkpoint)
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --reset
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--source` | Carpeta origen con las fotos (obligatorio) |
| `--dest` | Carpeta destino organizada (obligatorio) |
| `--config` | Fichero de configuración (default: `config.yaml`) |
| `--no-classify` | Omitir clasificación CLIP |
| `--no-duplicates` | Omitir detección de duplicados |
| `--no-gps` | Omitir geocodificación inversa GPS |
| `--only-inventory` | Solo generar inventario, sin copiar |
| `--event-gap` | Horas de brecha para separar eventos (default: 12) |
| `--reset` | Ignorar checkpoint y empezar desde cero |

## Rendimiento estimado (145.000 fotos / 200 GB)

| Fase | Tiempo estimado |
|------|----------------|
| Escaneo + EXIF | 20-30 min |
| Duplicados | 2-3 horas |
| Clasificación CLIP | 8-15 horas (CPU) |
| Geocodificación GPS | 5-10 min |
| Copia | depende del disco |

Con GPU Nvidia, CLIP se acelera ~10x automáticamente.

## Dependencias

Ver [requirements.txt](requirements.txt)

## Wiki

Consulta la [wiki del proyecto](wiki/) para documentación detallada:

- [Configuración](wiki/configuracion.md) — cómo personalizar categorías y ciudades
- [Cómo funciona la clasificación](wiki/clasificacion.md)
- [Checkpoint y rearranque](wiki/checkpoint.md)
- [Añadir nuevas ciudades](wiki/ciudades.md)
- [Solución de problemas](wiki/troubleshooting.md)
