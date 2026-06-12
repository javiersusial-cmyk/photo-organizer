# Solución de problemas

## Error: `AttributeError: 'BaseModelOutputWithPooling' object has no attribute 'norm'`

Versión reciente de `transformers` que cambia el tipo de retorno de `get_text_features`. Ya corregido en `core/classifier.py`. Si persiste, actualiza el código del repositorio.

## Advertencia: `You are sending unauthenticated requests to the HF Hub`

Es solo un aviso de velocidad de descarga. No afecta al funcionamiento. Puedes ignorarlo o crear una cuenta gratuita en huggingface.co y configurar el token:

```bash
# Windows
$env:HF_TOKEN = "tu_token_aqui"

# Linux/Mac
export HF_TOKEN="tu_token_aqui"
```

## La clasificación CLIP es lenta

Con CPU, CLIP procesa ~3-5 fotos por segundo. Para 145.000 fotos → 8-15 horas.

**Opciones para acelerar:**
1. Usar `--no-classify` si solo necesitas organizar por GPS y nombres de carpeta
2. Si tienes GPU Nvidia, instala `torch` con soporte CUDA:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```
3. Ejecutar en un PC con GPU

## Las fotos antiguas (antes de 2008) no tienen ciudad GPS

Las cámaras digitales antiguas y la mayoría de las compactas no graban GPS. Para estas fotos el sistema usa:
1. El nombre de la carpeta origen (si contiene una ciudad reconocida)
2. CLIP para la categoría temática

**Solución manual:** organiza las fotos antiguas en carpetas con nombres descriptivos antes de ejecutar el programa:
```
MisFotos/
├── 2005_Donostia/
├── 2005_Viaje_Roma/
└── 2006_Boda_Iker/
```

## Muchas fotos van a `Sin_clasificar`

CLIP tiene un umbral mínimo de confianza (0.20). Por debajo no asigna categoría.

Prueba a:
1. Añadir más frases descriptivas a las categorías en `config.yaml`
2. Bajar el umbral en `core/classifier.py` (línea `if best_score < 0.20`)

## El proceso se interrumpe por falta de memoria

La detección de duplicados carga todos los hashes en memoria. Con 145.000 fotos puede necesitar 3-4 GB de RAM.

**Opciones:**
- Usar `--no-duplicates` para omitir esta fase
- Ejecutar en una máquina con más RAM
- Procesar la colección en lotes (carpeta a carpeta)

## El inventario Excel no se abre

Asegúrate de tener `openpyxl` instalado:
```bash
pip install openpyxl
```

## Quiero reclasificar solo algunas carpetas

Por ahora el programa procesa toda la colección. Si tienes un checkpoint previo con metadatos ya extraídos, las fases rápidas se saltarán. Para reclasificar solo Eventos o Sin_clasificar, usa `--reset` y `--no-duplicates` para ir más rápido.
