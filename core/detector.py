"""
Clasificación en dos pasos:
  1. YOLO  → ¿hay personas en la foto?
  2. CLIP  → ¿qué tipo de escena/contexto es?

Combinando ambas señales se obtiene la categoría final:

  Personas + interior                  → Personas
  Personas + exterior + GPS            → Viajes/Ciudad
  Personas + exterior + sin GPS        → Personas
  Sin personas + urbano/monumento+GPS  → Ciudades/Ciudad
  Sin personas + urbano sin GPS        → Ciudades/Sin_ubicacion
  Sin personas + naturaleza            → Naturaleza
  Sin personas + lugar especifico+GPS  → Ciudades/Ciudad
  Resto                                → Sin_clasificar
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import numpy as np


# ── Contextos que reconoce CLIP ───────────────────────────────────────────────
CONTEXT_PROMPTS: dict[str, list[str]] = {
    "interior": [
        "indoor room interior",
        "inside a house or building",
        "living room or dining room",
        "office or workspace indoors",
        "kitchen bathroom bedroom",
    ],
    "urbano": [
        "city street with buildings",
        "urban architecture cityscape",
        "bridge over river in city",
        "town square or plaza",
        "historic building monument",
        "aerial view of city",
        "city waterfront promenade",
        "old town historic center",
    ],
    "naturaleza": [
        "nature landscape no buildings",
        "forest and trees countryside",
        "mountain landscape no city",
        "beach and ocean waves",
        "rural fields no buildings",
        "cave or rock formation nature",
        "river or lake in nature",
    ],
    "lugar_especial": [
        "famous landmark or monument",
        "tourist attraction architecture",
        "castle palace historic building",
        "church cathedral interior exterior",
        "museum or cultural building",
        "amusement park or stadium",
        "natural wonder cave waterfall",
    ],
}

# Umbral mínimo de confianza para aceptar un contexto
CONTEXT_THRESHOLD = 0.22

# Confianza mínima de YOLO para considerar que hay una persona
PERSON_CONFIDENCE = 0.40


class TwoStepClassifier:
    """
    Clasificador en dos pasos: YOLO (personas) + CLIP (contexto).
    """

    def __init__(self, fallback: str = "Sin_clasificar"):
        self.fallback       = fallback
        self._yolo          = None
        self._clip_model    = None
        self._clip_proc     = None
        self._text_features = None
        self._context_labels: list[str] = []

    def _load_yolo(self):
        from ultralytics import YOLO
        print("  Cargando YOLOv8 nano (detector de personas ~6 MB)...")
        self._yolo = YOLO("yolov8n.pt")

    def _load_clip(self):
        from transformers import CLIPModel, CLIPProcessor
        import torch

        print("  Cargando CLIP para análisis de contexto...")
        self._clip_proc  = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self._clip_model.eval()

        prompts = []
        for context, context_prompts in CONTEXT_PROMPTS.items():
            for p in context_prompts:
                prompts.append(p)
                self._context_labels.append(context)

        import torch
        inputs = self._clip_proc(
            text=prompts, return_tensors="pt", padding=True, truncation=True
        )
        with torch.no_grad():
            out = self._clip_model.get_text_features(**inputs)
            feats = out.pooler_output if hasattr(out, "pooler_output") else out
            self._text_features = feats / feats.norm(dim=-1, keepdim=True)

    def _has_person(self, path: Path) -> bool:
        """Devuelve True si YOLO detecta al menos una persona con suficiente confianza."""
        try:
            results = self._yolo(str(path), verbose=False, classes=[0])  # clase 0 = persona
            for r in results:
                for box in r.boxes:
                    if float(box.conf[0]) >= PERSON_CONFIDENCE:
                        return True
        except Exception:
            pass
        return False

    def _get_context(self, path: Path) -> Optional[str]:
        """Devuelve el contexto dominante de la imagen según CLIP."""
        import torch
        from PIL import Image

        try:
            image  = Image.open(path).convert("RGB")
            inputs = self._clip_proc(images=image, return_tensors="pt")
            with torch.no_grad():
                out  = self._clip_model.get_image_features(**inputs)
                feat = out.pooler_output if hasattr(out, "pooler_output") else out
                feat = feat / feat.norm(dim=-1, keepdim=True)

            sims       = (feat @ self._text_features.T).squeeze(0)
            best_idx   = int(sims.argmax())
            best_score = float(sims[best_idx])

            if best_score < CONTEXT_THRESHOLD:
                return None
            return self._context_labels[best_idx]
        except Exception:
            return None

    def classify(self, path: Path, gps_city: Optional[str] = None) -> tuple[str, Optional[str]]:
        """
        Devuelve (categoria, ciudad_o_None).

        Lógica:
          personas + interior                → ("Personas", None)
          personas + exterior + GPS          → ("Viajes", ciudad)
          personas + exterior + sin GPS      → ("Personas", None)
          sin personas + urbano/especial+GPS → ("Ciudades", ciudad)
          sin personas + urbano sin GPS      → ("Ciudades", "Sin_ubicacion")
          sin personas + naturaleza          → ("Naturaleza", None)
          resto                              → (fallback, None)
        """
        if self._yolo is None:
            self._load_yolo()
        if self._clip_model is None:
            self._load_clip()

        has_person = self._has_person(path)
        context    = self._get_context(path)

        if has_person:
            if context == "interior":
                return "Personas", None
            else:
                # Exterior con personas
                if gps_city:
                    return "Viajes", gps_city
                return "Personas", None
        else:
            if context in ("urbano", "lugar_especial"):
                if gps_city:
                    return "Ciudades", gps_city
                return "Ciudades", "Sin_ubicacion"
            elif context == "naturaleza":
                return "Naturaleza", None
            elif context == "interior":
                return "Personas", None  # interior sin personas detectadas → probablemente objetos del hogar
            else:
                if gps_city:
                    return "Ciudades", gps_city
                return self.fallback, None
