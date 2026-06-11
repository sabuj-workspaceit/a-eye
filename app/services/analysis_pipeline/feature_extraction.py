from __future__ import annotations

import cv2
import numpy as np


def extract_average_color(region: np.ndarray, mask: np.ndarray | None = None) -> dict[str, float]:
    if mask is not None:
        mean_bgr = cv2.mean(region, mask=mask)[:3]
        hsv_region = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        lab_region = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
        mean_hsv = cv2.mean(hsv_region, mask=mask)[:3]
        mean_lab = cv2.mean(lab_region, mask=mask)[:3]
    else:
        mean_bgr = np.mean(region, axis=(0, 1))
        hsv_region = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        lab_region = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
        mean_hsv = np.mean(hsv_region, axis=(0, 1))
        mean_lab = np.mean(lab_region, axis=(0, 1))

    return {
        "blue": float(mean_bgr[0]),
        "green": float(mean_bgr[1]),
        "red": float(mean_bgr[2]),
        "hue": float(mean_hsv[0]),
        "saturation": float(mean_hsv[1]),
        "value": float(mean_hsv[2]),
        "lab_l": float(mean_lab[0]),
        "lab_a": float(mean_lab[1]),
        "lab_b": float(mean_lab[2]),
    }


def extract_redness(region: np.ndarray, mask: np.ndarray | None = None) -> float:
    red_channel = region[:, :, 2].astype(float)
    green_channel = region[:, :, 1].astype(float)
    blue_channel = region[:, :, 0].astype(float)
    total = red_channel + green_channel + blue_channel + 1e-6
    redness_map = np.clip((red_channel - (green_channel + blue_channel) / 2) / total, 0.0, 1.0)
    
    if mask is not None:
        valid_pixels = redness_map[mask > 0]
        if valid_pixels.size == 0:
            return 0.0
        return float(np.mean(valid_pixels))
    
    return float(np.mean(redness_map))


def extract_texture_metrics(region: np.ndarray, mask: np.ndarray | None = None) -> dict[str, float]:
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    if mask is not None:
        mean_val, std_val = cv2.meanStdDev(gray, mask=mask)
        roughness = float(std_val[0][0])
    else:
        roughness = float(np.std(gray))
        
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    if mask is not None:
        mean_lap, std_lap = cv2.meanStdDev(np.abs(laplacian).astype(np.float32), mask=mask)
        uniformity = 1.0 / (1.0 + float(std_lap[0][0]))
    else:
        uniformity = 1.0 / (1.0 + float(np.std(laplacian)))
        
    return {
        "roughness": roughness,
        "uniformity": uniformity
    }


def extract_spots(region: np.ndarray, mask: np.ndarray | None = None) -> dict[str, object]:
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 5
    params.maxArea = 1000
    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False
    
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)
    
    if mask is not None:
        valid_kp = []
        for kp in keypoints:
            x, y = int(kp.pt[0]), int(kp.pt[1])
            if mask[y, x] > 0:
                valid_kp.append(kp)
        keypoints = valid_kp
        
    return {
        "spot_count": len(keypoints),
        "has_spots": len(keypoints) > 0
    }


def extract_cracks(region: np.ndarray, mask: np.ndarray | None = None) -> dict[str, object]:
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    
    _, thresh = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
    if mask is not None:
        thresh = cv2.bitwise_and(thresh, thresh, mask=mask)
        
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    crack_count = 0
    for cnt in contours:
        if len(cnt) >= 5:
            (x, y), (MA, ma), angle = cv2.fitEllipse(cnt)
            if ma > 0 and MA / ma > 2.5:
                crack_count += 1
                
    return {
        "crack_count": crack_count,
        "has_cracks": crack_count > 0
    }


def extract_zone_features(image: np.ndarray, zones: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    features: dict[str, dict[str, object]] = {}
    for zone in zones:
        name = zone["name"]
        x1, y1, x2, y2 = zone["coordinates"]
        region = image[y1:y2, x1:x2]
        if region.size == 0:
            features[name] = {
                "error": "empty zone",
                "coordinates": zone["coordinates"],
            }
            continue
            
        mask = None
        polygon = zone.get("polygon")
        if polygon:
            mask = np.zeros(region.shape[:2], dtype=np.uint8)
            offset_poly = np.array([[p[0] - x1, p[1] - y1] for p in polygon], dtype=np.int32)
            cv2.fillPoly(mask, [offset_poly], 255)

        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        if mask is not None:
            mean_brightness = cv2.mean(gray, mask=mask)[0]
        else:
            mean_brightness = float(np.mean(gray))

        features[name] = {
            "coordinates": zone["coordinates"],
            "average_color": extract_average_color(region, mask),
            "redness": extract_redness(region, mask),
            "brightness": float(mean_brightness),
            "texture_metrics": extract_texture_metrics(region, mask),
            "spots": extract_spots(region, mask),
            "cracks": extract_cracks(region, mask),
        }
    return features
