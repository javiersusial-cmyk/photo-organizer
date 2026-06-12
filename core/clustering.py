"""
Clustering visual de imágenes usando embeddings CLIP + DBSCAN.

En lugar de clasificar cada foto individualmente, agrupa fotos
visualmente similares aunque no tengan GPS ni nombre de carpeta descriptivo.

Flujo:
  1. Calcular embedding CLIP de cada imagen (vector de 512 dimensiones)
  2. Reducir dimensiones con UMAP (opcional, mejora calidad de clusters)
  3. Agrupar con DBSCAN (no necesita saber cuántos grupos hay de antemano)
  4. Intentar etiquetar cada cluster con una categoría via CLIP
  5. Devolver {path: "categoria/Cluster_01"} para fotos sin clasificación previa

Ventajas sobre clasificación individual:
  - Agrupa fotos del mismo sitio aunque no tengan GPS
  - Detecta automáticamente cuántos grupos hay
  - Fotos atípicas (outliers) van a Sin_clasificar en lugar de forzar una categoría

Dependencias adicionales:
  scikit-learn>=1.3   (DBSCAN, normalización)
  numpy>=1.24
  (umap-learn>=0.5   opcional, mejora calidad pero tarda más)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import numpy as np


# ── Parámetros DBSCAN ────────────────────────────────────────────────────────
# eps: distancia máxima entre dos puntos para ser vecinos (0-2, coseno normalizado)
#   Menor → clusters más compactos y numerosos
#   Mayor → clusters más grandes y generales
DEFAULT_EPS          = 0.35

# min_samples: mínimo de fotos para formar un cluster (grupos pequeños → outlier)
DEFAULT_MIN_SAMPLES  = 3

# Etiqueta DBSCAN para outliers
NOISE_LABEL = -1


class VisualClusterer:
    """
    Agrupa imágenes por similitud visual usando CLIP + DBSCAN.
    """

    def __init__(
        self,
        categories: dict[str, list[str]],
        fallback: str = "Sin_clasificar",
        eps: float = DEFAULT_EPS,
        min_samples: int = DEFAULT_MIN_SAMPLES,
        use_umap: bool = False,
    ):
        self.categories   = categories
        self.fallback     = fallback
        self.eps          = eps
        self.min_samples  = min_samples
        self.use_umap     = use_umap
        self._model       = None
        self._processor   = None
        self._text_feats  = None
        self._cat_labels: list[str] = []

    def _load_model(self):
        from transformers import CLIPModel, CLIPProcessor
        import torch

        print("  Cargando modelo CLIP para clustering...")
        self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self._model     = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self._model.eval()

        # Precalcular embeddings de texto para clasificar clusters
        prompts = []
        for cat, cat_prompts in self.categories.items():
            for p in cat_prompts:
                prompts.append(p)
                self._cat_labels.append(cat)

        import torch
        inputs = self._processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            out = self._model.get_text_features(**inputs)
            text_feats = out.pooler_output if hasattr(out, "pooler_output") else out
            self._text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)

    def _embed_images(self, paths: list[Path]) -> tuple[np.ndarray, list[Path]]:
        """
        Calcula los embeddings CLIP de todas las imágenes.
        Devuelve (matriz NxD, lista de paths válidos).
        """
        from PIL import Image
        import torch
        from tqdm import tqdm

        embeddings = []
        valid_paths = []

        for path in tqdm(paths, desc="  Calculando embeddings", unit="foto"):
            try:
                image  = Image.open(path).convert("RGB")
                inputs = self._processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    out  = self._model.get_image_features(**inputs)
                    feat = out.pooler_output if hasattr(out, "pooler_output") else out
                    feat = feat / feat.norm(dim=-1, keepdim=True)
                embeddings.append(feat.squeeze(0).numpy())
                valid_paths.append(path)
            except Exception:
                pass

        if not embeddings:
            return np.array([]), []

        return np.stack(embeddings), valid_paths

    def _label_cluster(self, cluster_embeddings: np.ndarray) -> str:
        """
        Etiqueta un cluster comparando el centroide con las categorías CLIP.
        """
        import torch

        centroid = cluster_embeddings.mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
        centroid_t = torch.tensor(centroid, dtype=torch.float32).unsqueeze(0)

        sims = (centroid_t @ self._text_feats.T).squeeze(0)
        best_idx   = int(sims.argmax())
        best_score = float(sims[best_idx])

        if best_score < 0.20:
            return self.fallback
        return self._cat_labels[best_idx]

    def cluster(
        self,
        paths: list[Path],
    ) -> dict[Path, str]:
        """
        Agrupa las imágenes y devuelve {path: "Categoria/Cluster_NN"}.

        Fotos outliers (no encajan en ningún cluster) → fallback/Sin_cluster.
        """
        if not paths:
            return {}

        if self._model is None:
            self._load_model()

        from sklearn.preprocessing import normalize
        from sklearn.cluster import DBSCAN

        # 1. Embeddings
        print(f"\n  Calculando embeddings de {len(paths)} fotos...")
        embeddings, valid_paths = self._embed_images(paths)
        if len(valid_paths) == 0:
            return {}

        # 2. Normalizar (distancia coseno)
        emb_norm = normalize(embeddings, norm="l2")

        # 3. Reducción dimensional opcional con UMAP
        if self.use_umap:
            try:
                import umap
                print("  Reduciendo dimensiones con UMAP...")
                reducer  = umap.UMAP(n_components=32, metric="cosine", random_state=42)
                emb_norm = reducer.fit_transform(emb_norm)
                emb_norm = normalize(emb_norm, norm="l2")
            except ImportError:
                print("  umap-learn no instalado, omitiendo reducción dimensional.")

        # 4. DBSCAN
        print(f"  Agrupando con DBSCAN (eps={self.eps}, min_samples={self.min_samples})...")
        db     = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="cosine")
        labels = db.fit_predict(emb_norm)

        unique_clusters = set(labels) - {NOISE_LABEL}
        print(f"  {len(unique_clusters)} clusters detectados "
              f"({(labels == NOISE_LABEL).sum()} fotos outlier)")

        # 5. Etiquetar cada cluster con una categoría
        cluster_categories: dict[int, str] = {}
        cluster_counter:    dict[str, int] = {}   # categoría → contador de clusters

        for cluster_id in sorted(unique_clusters):
            mask       = labels == cluster_id
            cat        = self._label_cluster(emb_norm[mask])
            count      = cluster_counter.get(cat, 0) + 1
            cluster_counter[cat] = count
            cluster_categories[cluster_id] = f"{cat}/Cluster_{count:02d}"

        # 6. Construir resultado
        result: dict[Path, str] = {}
        for path, label in zip(valid_paths, labels):
            if label == NOISE_LABEL:
                result[path] = f"{self.fallback}/Sin_cluster"
            else:
                result[path] = cluster_categories[label]

        # Resumen
        from collections import Counter
        cat_counts = Counter(result.values())
        print("\n  Distribución de clusters:")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"    {cat:<35} {count:>5} fotos")

        return result
