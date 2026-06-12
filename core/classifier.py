"""Clasificación temática de imágenes usando el modelo CLIP."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image


class PhotoClassifier:
    """
    Clasifica imágenes en categorías temáticas usando CLIP.
    El modelo se descarga la primera vez (~1.5 GB) y queda en caché.
    """

    def __init__(self, categories: Dict[str, List[str]], fallback: str = "Sin_clasificar"):
        self.categories = categories
        self.fallback = fallback
        self._model = None
        self._processor = None
        self._text_features = None
        self._labels: List[str] = []   # categoría para cada prompt
        self._prompts: List[str] = []

    def _load_model(self):
        """Carga CLIP en memoria (lazy, solo la primera vez)."""
        from transformers import CLIPModel, CLIPProcessor
        import torch

        print("  Cargando modelo CLIP (solo la primera vez)...")
        self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self._model.eval()

        # Precalcular embeddings de texto para todos los prompts
        for category, prompts in self.categories.items():
            for prompt in prompts:
                self._prompts.append(prompt)
                self._labels.append(category)

        inputs = self._processor(
            text=self._prompts, return_tensors="pt", padding=True, truncation=True
        )
        import torch
        with torch.no_grad():
            raw = self._model.get_text_features(**inputs)
            # En versiones recientes de transformers puede devolver un objeto con pooler_output
            text_tensor = raw.pooler_output if hasattr(raw, "pooler_output") else raw
            self._text_features = text_tensor / text_tensor.norm(dim=-1, keepdim=True)

    def classify(self, path: Path) -> str:
        """Devuelve la categoría temática de la imagen."""
        if self._model is None:
            self._load_model()

        import torch

        try:
            image = Image.open(path).convert("RGB")
            inputs = self._processor(images=image, return_tensors="pt")
            with torch.no_grad():
                raw = self._model.get_image_features(**inputs)
                image_features = raw.pooler_output if hasattr(raw, "pooler_output") else raw
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Similitud coseno con todos los prompts
            similarities = (image_features @ self._text_features.T).squeeze(0)
            best_idx = int(similarities.argmax())
            best_score = float(similarities[best_idx])

            # Umbral mínimo de confianza
            if best_score < 0.20:
                return self.fallback

            return self._labels[best_idx]

        except Exception:
            return self.fallback
