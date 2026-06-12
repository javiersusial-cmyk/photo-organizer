# Clustering visual

El clustering visual agrupa fotos por similitud visual usando IA, sin necesidad de GPS ni nombres de carpeta descriptivos. Es especialmente útil para fotos antiguas de cámaras sin GPS.

## Cómo funciona

```
1. Calcular embedding CLIP de cada imagen (vector de 512 números que describe visualmente la foto)
2. Agrupar vectores cercanos con DBSCAN (fotos visualmente similares → mismo grupo)
3. Etiquetar cada grupo con la categoría CLIP más probable (Viajes, Personas, Naturaleza...)
4. Resultado: Personas/Cluster_01, Viajes/Cluster_02, Naturaleza/Cluster_03...
```

A diferencia de la clasificación individual, aquí **las fotos se comparan entre sí**: si 20 fotos de una playa concreta tienen embeddings parecidos, van al mismo cluster aunque ninguna tenga GPS.

## Cuándo se activa

Solo actúa sobre fotos que **no han podido clasificarse** por ningún otro método:
- Sin coordenadas GPS
- Sin pista en el nombre de carpeta origen
- CLIP individual no ha superado el umbral de confianza (van a `Sin_clasificar`)

Las fotos ya clasificadas por GPS o nombre de carpeta no se tocan.

## Uso

```bash
# Activar clustering con parámetros por defecto
python run.py --source "D:\MisFotos" --dest "D:\FotosOrganizadas" --cluster

# Ajustar sensibilidad (menor eps = clusters más compactos y numerosos)
python run.py --source ... --dest ... --cluster --cluster-eps 0.25

# Mínimo de fotos para formar un cluster
python run.py --source ... --dest ... --cluster --cluster-min 5
```

## Estructura de salida

```
FotosOrganizadas/
├── 2005/
│   ├── Personas/
│   │   ├── Cluster_01/   ← grupo de fotos similares (ej: misma reunión)
│   │   └── Cluster_02/   ← otro grupo de personas
│   ├── Viajes/
│   │   └── Cluster_01/   ← fotos de exteriores similares
│   └── Sin_clasificar/
│       └── Sin_cluster/  ← fotos outlier que no encajan en ningún grupo
```

## Parámetros

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--cluster-eps` | Distancia máxima entre fotos del mismo cluster (0-2) | 0.35 |
| `--cluster-min` | Mínimo de fotos para formar un cluster | 3 |

**Guía de `--cluster-eps`:**
- `0.20` → clusters muy compactos (fotos casi idénticas juntas)
- `0.35` → equilibrado (recomendado)
- `0.50` → clusters grandes y generales

## Dependencias

```bash
pip install scikit-learn numpy
pip install umap-learn  # opcional, mejora la calidad del clustering
```

## Rendimiento

El clustering calcula un embedding por foto (igual que la clasificación CLIP normal) y luego ejecuta DBSCAN, que es muy rápido. El coste adicional sobre la clasificación normal es mínimo.
