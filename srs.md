Below is the structure I would give to Codex/Claude/OpenAI as the foundation document for building the FastAPI AI service.

---

# A-EYE AI Analysis Service

## Software Requirements Specification (SRS)

### Version 1.0

---

# 1. Project Goal

## Purpose

Build a production-ready FastAPI service responsible for analyzing wellness images submitted by users.

The service must:

1. Receive iris, tongue, and facial images
2. Validate image quality
3. Detect the target region
4. Normalize the image
5. Apply practitioner-defined zone maps
6. Extract visual observations from each zone
7. Execute practitioner-defined rules
8. Generate structured findings
9. Generate practitioner and client reports
10. Return results to the main application

The service does not diagnose disease.

The service only:

* detects visual characteristics
* maps them to practitioner-defined zones
* applies practitioner-defined interpretation rules
* generates wellness-oriented findings

---

# 2. Scope

The FastAPI service is responsible only for:

* image analysis
* computer vision
* rule execution
* report generation

The service is NOT responsible for:

* authentication
* payments
* subscriptions
* user management
* notifications
* admin management

Those responsibilities belong to the NestJS backend.

---

# 3. Supported Scan Types

## Iris

Required:

* left eye
* right eye

Analysis:

* iris detection
* pupil detection
* zone mapping
* feature extraction

---

## Tongue

Required:

* single tongue image

Analysis:

* tongue segmentation
* color normalization
* zone mapping
* feature extraction

---

## Face

Required:

* full face image

Analysis:

* face mesh detection
* facial landmark extraction
* zone mapping
* feature extraction

---

# 4. AI Pipeline

Every scan must execute the following pipeline.

```text
Image Upload
↓
Quality Validation
↓
Region Detection
↓
Normalization
↓
Zone Mapping
↓
Feature Extraction
↓
Rule Engine
↓
Finding Generation
↓
Report Generation
↓
Response
```

---

# 5. Image Quality Validation

The service must reject invalid images.

---

## Blur Detection

Method:

```python
Variance of Laplacian
```

Configurable threshold:

```python
100
```

Return:

```json
{
  "valid": false,
  "reason": "Image blurry"
}
```

---

## Lighting Validation

Detect:

* underexposed
* overexposed

Metrics:

* brightness histogram
* average intensity

---

## Glare Detection

Detect:

* flash reflections
* iris reflections
* bright spots

---

## Framing Validation

Verify:

### Iris

* entire iris visible
* pupil visible

### Tongue

* full tongue visible

### Face

* forehead visible
* chin visible

---

# 6. Region Detection

---

## Iris Detection

Technology:

```text
OpenCV
```

Detection:

```text
Hough Circle Transform
```

Required outputs:

```json
{
  "iris_center_x": 100,
  "iris_center_y": 100,
  "iris_radius": 50
}
```

---

## Tongue Detection

Technology:

```text
TensorFlow Lite
```

Detection:

```text
Segmentation
```

Output:

```json
{
  "mask": "binary_mask"
}
```

---

## Face Detection

Technology:

```text
MediaPipe Face Mesh
```

Required:

```text
468 landmarks
```

Output:

```json
{
  "landmarks": [...]
}
```

---

# 7. Image Normalization

Purpose:

Create standardized analysis input.

---

## Iris

Normalize:

```text
size
rotation
brightness
contrast
```

Output:

```text
512x512
```

---

## Tongue

Normalize:

```text
white balance
size
brightness
```

Output:

```text
512x512
```

---

## Face

Normalize:

```text
alignment
brightness
contrast
```

Output:

```text
512x512
```

---

# 8. Zone Mapping System

The service must support practitioner-defined zone maps.

---

# Zone Map Model

```json
{
  "id": "zone_1",
  "scan_type": "iris",
  "name": "liver_zone",
  "shape_type": "polygon",
  "coordinates": []
}
```

---

# Iris Zones

Support:

```text
36 zones
3 rings
12 segments
```

Zone generation should be mathematical.

No manual drawing required.

---

# Tongue Zones

Support:

```text
polygon zones
```

Example:

```text
tip
center
left
right
rear
```

---

# Face Zones

Support:

```text
forehead
left cheek
right cheek
nose
mouth
chin
eye regions
```

Based on MediaPipe landmarks.

---

# 9. Feature Extraction

The service must extract observations from each zone.

---

# Supported Features

## Color

Extract:

```text
RGB
HSV
LAB
```

Metrics:

```text
redness
brightness
saturation
```

---

## Texture

Metrics:

```text
roughness
uniformity
contrast
```

Methods:

```text
GLCM
LBP
```

---

## Spot Detection

Detect:

```text
dark spots
light spots
```

---

## Crack Detection

Detect:

```text
surface cracks
tongue fissures
```

---

## Symmetry Analysis

Compare:

```text
left vs right
```

---

# Observation Output

```json
{
  "zone": "center",
  "redness": 0.83,
  "brightness": 0.54,
  "texture": 0.74,
  "spots": 2,
  "cracks": true
}
```

---

# 10. Rule Engine

Purpose:

Convert observations into findings.

---

# Rule Structure

```json
{
  "scan_type": "tongue",
  "zone": "center",
  "condition": "redness > 0.7",
  "finding": "digestive stress pattern"
}
```

---

# Supported Operators

```text
>
<
>=
<=
==
!=
AND
OR
```

---

# Rule Output

```json
{
  "zone": "center",
  "finding": "digestive stress pattern"
}
```

---

# 11. Protocol Engine

Purpose:

Attach recommendations.

---

# Example

```json
{
  "finding": "digestive stress pattern",
  "recommendations": [
    "increase hydration",
    "reduce processed foods"
  ]
}
```

---

# 12. Report Generation

The service must generate:

## Practitioner Report

Contains:

* images
* zone observations
* extracted features
* findings
* recommendations
* compliance log

---

## Client Report

Contains:

* simplified findings
* recommendations
* wellness disclaimer

Must never include:

```text
diagnosis
treatment
cure
prescription
medical advice
```

---

# 13. LLM Integration

Purpose:

Convert structured findings into readable language.

Input:

```json
{
  "findings": []
}
```

Output:

```text
Human-readable wellness summary
```

---

# 14. Safety Filter

Must scan all generated text.

Blocked words:

```text
diagnose
diagnosis
treat
treatment
cure
prescribe
prescription
medical advice
```

---

# 15. API Endpoints

## Health

```http
GET /health
```

---

## Analyze Iris

```http
POST /analyze/iris
```

Input:

```text
left_eye
right_eye
zone_map_id
```

---

## Analyze Tongue

```http
POST /analyze/tongue
```

Input:

```text
image
zone_map_id
```

---

## Analyze Face

```http
POST /analyze/face
```

Input:

```text
image
zone_map_id
```

---

## Generate Report

```http
POST /reports/generate
```

---

# 16. Database Models

Required models:

```text
zone_maps
zone_regions
rules
findings
observations
protocols
reports
report_sections
analysis_jobs
```

---

# 17. Performance Requirements

Image Validation:

```text
< 2 seconds
```

Single Scan Analysis:

```text
< 15 seconds
```

Full Report Generation:

```text
< 30 seconds
```

---

# 18. Non-Functional Requirements

* Dockerized deployment
* Async FastAPI endpoints
* PostgreSQL support
* Redis queue support
* AWS S3 support
* Structured logging
* OpenTelemetry support
* Unit tests
* Integration tests
* OpenAPI documentation
* Production-ready architecture
* Horizontal scalability

---

# Expected Deliverable

A standalone FastAPI microservice that accepts iris, tongue, and face images, performs computer vision analysis, executes practitioner-defined zone and rule logic, and returns structured wellness findings and reports through REST APIs.
