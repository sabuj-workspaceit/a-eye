from __future__ import annotations

import cv2
import numpy as np


def is_blurry(image: np.ndarray, threshold: float = 100.0) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return bool(laplacian_var < threshold)


def lighting_score(image: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    std = float(gray.std())
    return {"average_brightness": mean, "contrast": std}


def detect_glare(image: np.ndarray, threshold: int = 220, area_ratio: float = 0.05) -> dict[str, object]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, bright_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    bright_fraction = float(np.count_nonzero(bright_mask) / bright_mask.size)
    return {
        "glare_fraction": bright_fraction,
        "has_glare": bool(bright_fraction > area_ratio),
        "threshold": threshold,
    }


def framing_score(image: np.ndarray, min_border_fraction: float = 0.10) -> dict[str, object]:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    border_pixels = int(min_border_fraction * min(height, width))
    border_area = edges[:border_pixels, :].sum() + edges[-border_pixels:, :].sum() + edges[:, :border_pixels].sum() + edges[:, -border_pixels:].sum()
    return {"border_strength": float(border_area), "min_border_fraction": min_border_fraction}


def validate_image(image: np.ndarray) -> dict[str, object]:
    return {
        "blur": {
            "is_blurry": is_blurry(image),
        },
        "lighting": lighting_score(image),
        "glare": detect_glare(image),
        "framing": framing_score(image),
    }
