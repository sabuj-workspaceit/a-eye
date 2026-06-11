from __future__ import annotations

import cv2
import numpy as np


def normalize_image(image: np.ndarray, target_size: tuple[int, int] = (512, 512)) -> np.ndarray:
    if image is None:
        raise ValueError("Image must not be None")

    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    equalized_l = cv2.equalizeHist(l)
    lab = cv2.merge((equalized_l, a, b))
    normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return normalized
