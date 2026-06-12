# Configuración

Toda la configuración se gestiona en el fichero `config.yaml` en la raíz del proyecto.

## Extensiones soportadas

```yaml
extensions:
  - .jpg
  - .jpeg
  - .png
  - .heic   # iPhone
  - .cr2    # Canon RAW
  - .nef    # Nikon RAW
  - .arw    # Sony RAW
```

Añade o quita extensiones según tu cámara.

## Categorías temáticas

Cada categoría tiene una lista de frases en inglés que CLIP usará para reconocer imágenes similares.

```yaml
categories:
  Viajes:
    - "travel photo"
    - "landscape travel"
    - "tourist attraction"
  Personas:
    - "portrait of a person"
    - "group of people"
```

**Consejo:** usa frases descriptivas en inglés, no solo palabras sueltas. CLIP entiende contexto.

## Parámetros de duplicados

```yaml
duplicate_threshold: 10   # 0=idénticos, 10=muy similares, 20=similares
copy_duplicates: true     # copiar duplicados a _Duplicados para revisión
```

## Parámetros de carpetas especiales

```yaml
fallback_category: Sin_clasificar   # categoría cuando CLIP no está seguro
duplicates_folder: _Duplicados      # nombre de la carpeta de duplicados
fallback_year: Sin_fecha            # año para fotos sin fecha EXIF
```

## Brecha entre eventos

Configurable también por línea de comandos con `--event-gap`:

```bash
python run.py --source ... --dest ... --event-gap 24
```

Por defecto: 12 horas.
