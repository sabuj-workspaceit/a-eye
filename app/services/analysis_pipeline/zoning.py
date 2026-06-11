from __future__ import annotations

import numpy as np


import cv2

def generate_zones(image: np.ndarray, scan_type: str, landmarks: list[dict[str, float]] | None = None, detection_results: dict[str, object] | None = None) -> list[dict[str, object]]:
    height, width = image.shape[:2]
    zones = [
        {
            "name": "center",
            "coordinates": [
                int(width * 0.25),
                int(height * 0.25),
                int(width * 0.75),
                int(height * 0.75),
            ],
        },
        {
            "name": "top_left",
            "coordinates": [0, 0, int(width * 0.5), int(height * 0.5)],
        },
        {
            "name": "bottom_right",
            "coordinates": [int(width * 0.5), int(height * 0.5), width, height],
        },
    ]

    if scan_type.lower() == "iris":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=height/4,
            param1=100,
            param2=30,
            minRadius=int(height * 0.2),
            maxRadius=int(height * 0.8)
        )
        if circles is not None:
            circles = np.uint16(np.around(circles))
            cx, cy, r_iris = circles[0][0]
        else:
            cx, cy = width // 2, height // 2
            r_iris = min(width, height) // 2

        r_pupil = r_iris * 0.35
        r_step = (r_iris - r_pupil) / 3.0
        
        iris_zones = []
        for ring in range(3):
            r_inner = r_pupil + ring * r_step
            r_outer = r_pupil + (ring + 1) * r_step
            for segment in range(12):
                start_angle = segment * 30
                end_angle = (segment + 1) * 30
                
                angles_inner = np.linspace(start_angle, end_angle, 5)
                angles_outer = np.linspace(end_angle, start_angle, 5)
                
                poly_points = []
                for angle in angles_inner:
                    rad = np.radians(angle)
                    x = int(cx + r_inner * np.sin(rad))
                    y = int(cy - r_inner * np.cos(rad))
                    poly_points.append([x, y])
                for angle in angles_outer:
                    rad = np.radians(angle)
                    x = int(cx + r_outer * np.sin(rad))
                    y = int(cy - r_outer * np.cos(rad))
                    poly_points.append([x, y])
                
                xs = [p[0] for p in poly_points]
                ys = [p[1] for p in poly_points]
                bbox = [max(0, min(xs)), max(0, min(ys)), min(width, max(xs)), min(height, max(ys))]
                
                iris_zones.append({
                    "name": f"ring_{ring+1}_segment_{segment+1}",
                    "coordinates": bbox,
                    "polygon": poly_points
                })
        return iris_zones

    if scan_type.lower() == "face":
        if landmarks:
            pts = np.array([[lm["x"], lm["y"]] for lm in landmarks], dtype=np.int32)
            face_zones = []

            def add_zone(name, indices):
                if not indices: return
                zone_pts = pts[indices]
                if len(zone_pts) < 3:
                    return
                hull = cv2.convexHull(zone_pts)
                poly_points = hull.reshape(-1, 2).tolist()
                xs = [p[0] for p in poly_points]
                ys = [p[1] for p in poly_points]
                bbox = [max(0, min(xs)), max(0, min(ys)), min(width, max(xs)), min(height, max(ys))]
                face_zones.append({
                    "name": name,
                    "coordinates": bbox,
                    "polygon": poly_points
                })
                
            min_y, max_y = np.min(pts[:, 1]), np.max(pts[:, 1])
            min_x, max_x = np.min(pts[:, 0]), np.max(pts[:, 0])
            h = max_y - min_y
            w = max_x - min_x
            
            forehead_idx = [i for i, p in enumerate(pts) if p[1] < min_y + h * 0.25]
            chin_idx = [i for i, p in enumerate(pts) if p[1] > min_y + h * 0.85]
            nose_idx = [i for i, p in enumerate(pts) if min_y + h * 0.4 < p[1] < min_y + h * 0.6 and min_x + w * 0.4 < p[0] < min_x + w * 0.6]
            left_cheek_idx = [i for i, p in enumerate(pts) if min_y + h * 0.4 < p[1] < min_y + h * 0.75 and p[0] < min_x + w * 0.4]
            right_cheek_idx = [i for i, p in enumerate(pts) if min_y + h * 0.4 < p[1] < min_y + h * 0.75 and p[0] > min_x + w * 0.6]
            mouth_idx = [i for i, p in enumerate(pts) if min_y + h * 0.65 < p[1] < min_y + h * 0.85 and min_x + w * 0.35 < p[0] < min_x + w * 0.65]

            add_zone("forehead", forehead_idx)
            add_zone("chin", chin_idx)
            add_zone("nose", nose_idx)
            add_zone("left_cheek", left_cheek_idx)
            add_zone("right_cheek", right_cheek_idx)
            add_zone("mouth", mouth_idx)
            
            if face_zones:
                return face_zones

        return zones[:2]
    if scan_type.lower() == "tongue":
        bbox = None
        if detection_results and "tongue" in detection_results:
            bbox = detection_results["tongue"].get("bbox")
            
        if not bbox:
            bbox = [int(width*0.3), int(height*0.2), int(width*0.7), int(height*0.8)]
            
        x1, y1, x2, y2 = bbox
        bw = x2 - x1
        bh = y2 - y1
        
        # Partitioning based on vertical orientation (assuming tip is at the bottom, rear is at the top)
        # Tip: Lowest 20%
        # Rear: Top 20%
        # Center: middle 60% vertically, middle 60% horizontally
        # Left: left 20% horizontally, middle 60% vertically
        # Right: right 20% horizontally, middle 60% vertically
        
        tongue_zones = [
            {
                "name": "tip",
                "coordinates": [x1, y1 + int(bh * 0.8), x2, y2]
            },
            {
                "name": "rear",
                "coordinates": [x1, y1, x2, y1 + int(bh * 0.2)]
            },
            {
                "name": "center",
                "coordinates": [x1 + int(bw * 0.2), y1 + int(bh * 0.2), x1 + int(bw * 0.8), y1 + int(bh * 0.8)]
            },
            {
                "name": "left",
                "coordinates": [x1, y1 + int(bh * 0.2), x1 + int(bw * 0.2), y1 + int(bh * 0.8)]
            },
            {
                "name": "right",
                "coordinates": [x1 + int(bw * 0.8), y1 + int(bh * 0.2), x2, y1 + int(bh * 0.8)]
            }
        ]
        return tongue_zones
        
    return zones
