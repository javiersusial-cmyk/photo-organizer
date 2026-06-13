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
    "comida": [
        "food on a plate close up",
        "a meal at a restaurant table",
        "dessert cake or pastry",
        "cooked dish or tapas",
    ],
    "animales": [
        "a dog or cat pet close up",
        "a wild animal",
        "a bird",
        "a farm animal like horse or cow",
    ],
    "documento": [
        "a document or paper with text",
        "a screenshot of a computer screen",
        "a whiteboard or sign with writing",
        "a receipt ticket or invoice",
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

    def __init__(self, fallback: str = "Sin_clasificar", detect_landmarks: bool = False,
                 landmark_threshold: Optional[float] = None):
        self.fallback           = fallback
        self.detect_landmarks   = detect_landmarks
        self.landmark_threshold = landmark_threshold
        self._yolo             = None
        self._clip_model       = None
        self._clip_proc        = None
        self._text_features    = None
        self._context_labels: list[str] = []
        self._landmark_features = None
        self._landmark_cities: list[str] = []

    def _load_yolo(self):
        from ultralytics import YOLO
        print("  Cargando YOLOv8 nano (detector de personas ~6 MB)...")
        self._yolo = YOLO("yolov8n.pt")

    def _embed_text(self, prompts: list[str]):
        """Calcula embeddings normalizados de una lista de prompts."""
        import torch
        inputs = self._clip_proc(
            text=prompts, return_tensors="pt", padding=True, truncation=True
        )
        with torch.no_grad():
            out   = self._clip_model.get_text_features(**inputs)
            feats = out.pooler_output if hasattr(out, "pooler_output") else out
            return feats / feats.norm(dim=-1, keepdim=True)

    def _load_clip(self):
        from transformers import CLIPModel, CLIPProcessor

        print("  Cargando CLIP para análisis de contexto y monumentos...")
        self._clip_proc  = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self._clip_model.eval()

        # Embeddings de contexto
        prompts = []
        for context, context_prompts in CONTEXT_PROMPTS.items():
            for p in context_prompts:
                prompts.append(p)
                self._context_labels.append(context)
        self._text_features = self._embed_text(prompts)

        # Embeddings de monumentos famosos
        if self.detect_landmarks:
            from core.landmarks import LANDMARKS
            lm_prompts = []
            for prompt, city in LANDMARKS.items():
                lm_prompts.append(prompt)
                self._landmark_cities.append(city)
            self._landmark_features = self._embed_text(lm_prompts)

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

    def _image_feature(self, path: Path):
        """Calcula el embedding normalizado de la imagen una sola vez (o None)."""
        import torch
        from PIL import Image
        try:
            image  = Image.open(path).convert("RGB")
            inputs = self._clip_proc(images=image, return_tensors="pt")
            with torch.no_grad():
                out  = self._clip_model.get_image_features(**inputs)
                feat = out.pooler_output if hasattr(out, "pooler_output") else out
                return feat / feat.norm(dim=-1, keepdim=True)
        except Exception:
            return None

    def _context_from_feature(self, feat) -> Optional[str]:
        """Devuelve el contexto dominante a partir del embedding de imagen."""
        if feat is None:
            return None
        sims       = (feat @ self._text_features.T).squeeze(0)
        best_idx   = int(sims.argmax())
        best_score = float(sims[best_idx])
        if best_score < CONTEXT_THRESHOLD:
            return None
        return self._context_labels[best_idx]

    def _landmark_from_feature(self, feat) -> Optional[str]:
        """Devuelve la ciudad de un monumento reconocido, o None."""
        if feat is None or self._landmark_features is None:
            return None
        from core.landmarks import LANDMARK_THRESHOLD
        thr = self.landmark_threshold if self.landmark_threshold is not None else LANDMARK_THRESHOLD
        sims       = (feat @ self._landmark_features.T).squeeze(0)
        best_idx   = int(sims.argmax())
        best_score = float(sims[best_idx])
        if best_score < thr:
            return None
        return self._landmark_cities[best_idx]

    def _person_area_ratio(self, path: Path) -> float:
        """Devuelve el ratio del área de la persona más grande respecto a la imagen (0-1)."""
        try:
            from PIL import Image as PILImage
            img_w, img_h = PILImage.open(path).size
            img_area = img_w * img_h
            results = self._yolo(str(path), verbose=False, classes=[0])
            max_ratio = 0.0
            for r in results:
                for box in r.boxes:
                    if float(box.conf[0]) >= PERSON_CONFIDENCE:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        ratio = ((x2 - x1) * (y2 - y1)) / img_area
                        max_ratio = max(max_ratio, ratio)
            return max_ratio
        except Exception:
            return 0.0

    def classify(
        self,
        path: Path,
        gps_city: Optional[str] = None,
        hint_city: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        """
        Devuelve (categoria, ciudad_o_None).

        Lógica:
          lugar_especial/urbano              → Ciudades/ciudad (persona secundaria no cambia esto)
          personas dominantes + interior     → Personas
          personas dominantes + exterior+ciudad → Viajes/ciudad
          personas dominantes + exterior sin ciudad → Personas
          naturaleza                         → Naturaleza
          sin contexto claro + ciudad        → Ciudades/ciudad
          resto                              → fallback

        La ciudad se resuelve por: GPS > hint de carpeta > monumento reconocido.
        """
        if self._yolo is None:
            self._load_yolo()
        if self._clip_model is None:
            self._load_clip()

        feat         = self._image_feature(path)
        context      = self._context_from_feature(feat)
        person_ratio = self._person_area_ratio(path)
        person_dominant = person_ratio >= 0.10   # persona ocupa >10% de la imagen

        # Ciudad: GPS > hint carpeta > monumento reconocido por CLIP
        city = gps_city or hint_city
        if not city:
            city = self._landmark_from_feature(feat)

        # 0. Documentos / Comida / Animales → primeros planos, máxima prioridad
        if context == "documento":
            return "Documentos", None
        if context == "comida" and not person_dominant:
            return "Comida", None
        if context == "animales" and not person_dominant:
            return "Animales", None

        # 1. Lugar especial o urbano → siempre Ciudades, independiente de personas
        if context in ("lugar_especial", "urbano"):
            if city:
                return "Ciudades", city
            return "Ciudades", "Sin_ubicacion"

        # 2. Persona dominante
        if person_dominant:
            if context == "interior":
                return "Personas", None
            # Exterior con persona dominante: si hay ciudad reconocida → Viajes
            if city:
                return "Viajes", city
            return "Personas", None

        # 3. Naturaleza sin persona dominante
        if context == "naturaleza":
            # Si reconoció un monumento pese a parecer naturaleza, prevalece la ciudad
            if city and city not in (gps_city, hint_city):
                return "Ciudades", city
            return "Naturaleza", None

        # 4. Interior sin persona dominante → Hogar (habitaciones, objetos, mobiliario)
        if context == "interior":
            return "Hogar", None

        # 5. Sin contexto claro pero con ciudad → Ciudades
        if city:
            return "Ciudades", city

        # 6. Sin nada clasificable
        return self.fallback, None
