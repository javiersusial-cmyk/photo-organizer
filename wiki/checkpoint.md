# Checkpoint y rearranque

Con colecciones grandes (decenas de miles de fotos) el proceso puede tardar horas. El sistema de checkpoint permite interrumpirlo y reanudarlo sin perder el trabajo hecho.

## Cómo funciona

El fichero `checkpoint.json` se guarda en la carpeta destino y se actualiza continuamente:

| Fase | Frecuencia de guardado |
|------|----------------------|
| Metadatos EXIF | Tras cada foto |
| Duplicados | Al completar la fase |
| Clasificación CLIP | Cada 500 fotos |
| Copia de ficheros | Cada 200 fotos |

## Reanudar tras una interrupción

Simplemente vuelve a lanzar **el mismo comando**:

```bash
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas"
```

El programa detecta el checkpoint automáticamente e informa de las fases ya completadas:

```
Checkpoint encontrado. Fases completadas: ['metadata', 'duplicates']
[3/5] Duplicados (checkpoint) — restaurando...
      1234 duplicados restaurados
[4/5] Clasificando imágenes...
  → CLIP: 8500 ya clasificadas (checkpoint). Clasificando 36500 restantes...
```

## Empezar desde cero

```bash
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --reset
```

## Dónde está el checkpoint

```
FotosOrganizadas/
└── checkpoint.json   ← se elimina automáticamente al terminar con éxito
```

## ¿Qué pasa si el checkpoint está corrupto?

Usa `--reset` para ignorarlo y empezar desde cero. También puedes eliminar manualmente el fichero `checkpoint.json`.
