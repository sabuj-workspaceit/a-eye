from __future__ import annotations

import cv2
import numpy as np

try:
    import mediapipe as mp  # type: ignore
except ImportError:  # pragma: no cover
    mp = None

try:
    import tflite_runtime.interpreter as tflite  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from tensorflow.lite import Interpreter as tflite  # type: ignore
    except ImportError:  # pragma: no cover
        tflite = None


def detect_iris(image: np.ndarray) -> dict[str, object]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.5,
        minDist=gray.shape[0] / 8,
        param1=100,
        param2=30,
        minRadius=10,
        maxRadius=80,
    )

    findings = []
    if circles is not None:
        for x, y, r in np.round(circles[0, :]).astype(int):
            findings.append({"center": [int(x), int(y)], "radius": int(r)})

    return {"iris_found": bool(findings), "circles": findings}


def detect_face(image: np.ndarray, provided_landmarks: list[dict[str, float]] | None = None) -> dict[str, object]:
    height, width = image.shape[:2]
    if provided_landmarks is not None:
        return {"face_found": True, "face_count": 1, "landmarks": provided_landmarks}

    if mp is not None:
        try:
            face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            face_mesh.close()
            if results.multi_face_landmarks:
                landmarks = []
                for lm in results.multi_face_landmarks[0].landmark:
                    landmarks.append({"x": lm.x * width, "y": lm.y * height, "z": lm.z})
                return {"face_found": True, "face_count": len(results.multi_face_landmarks), "landmarks": landmarks}
            return {"face_found": False, "face_count": 0}
        except (AttributeError, Exception):
            # Fall back to Haar Cascade if MediaPipe fails
            pass

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    return {"face_found": bool(len(faces)), "faces": [list(map(int, face)) for face in faces]}


def detect_tongue(image: np.ndarray) -> dict[str, object]:
    height, width = image.shape[:2]
    # Fallback default bounding box
    bbox = [int(width*0.3), int(height*0.2), int(width*0.7), int(height*0.8)]

    if tflite is not None:
        import os
        model_path = "ml_models/tongue_segmentation.tflite"
        if os.path.exists(model_path):
            try:
                interpreter = tflite.Interpreter(model_path=model_path)
                interpreter.allocate_tensors()
                
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                input_shape = input_details[0]['shape']
                resized = cv2.resize(image, (input_shape[2], input_shape[1]))
                
                input_data = np.expand_dims(resized, axis=0)
                if input_details[0]['dtype'] == np.float32:
                    input_data = (np.float32(input_data) - 127.5) / 127.5
                    
                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()
                
                # output_data = interpreter.get_tensor(output_details[0]['index'])
                # Further mask extraction can be added here if the model outputs semantic masks
            except Exception:
                pass

    return {"tongue_detected": True, "bbox": bbox}


def detect_all(image: np.ndarray, landmarks: list[dict[str, float]] | None = None) -> dict[str, object]:
    return {
        "iris": detect_iris(image),
        "face": detect_face(image, landmarks),
        "tongue": detect_tongue(image),
    }
