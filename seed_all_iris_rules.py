import requests

BASE_URL = "http://localhost:8000/api/v1/practitioner"

def seed_all_iris_rules():
    print("Seeding ALL 36 Iris Rules...")
    
    # 1. Create or get ZoneMap
    maps_res = requests.get(f"{BASE_URL}/zone-maps?scan_type=iris")
    maps = maps_res.json().get("data", {}).get("items", [])
    
    if not maps:
        res = requests.post(f"{BASE_URL}/zone-maps", json={
            "name": "Iris Standard Map",
            "scan_type": "iris"
        })
        map_id = res.json().get("data", {}).get("id") or res.json().get("id")
    else:
        map_id = maps[0]["id"]
        
    # Delete all existing Iris rules
    rules_res = requests.get(f"{BASE_URL}/rules?scan_type=iris")
    existing_rules = rules_res.json().get("data", {}).get("items", [])
    for r in existing_rules:
        requests.delete(f"{BASE_URL}/rules/{r['id']}")
    print("Cleared old rules.")

    # 2. Define 36 rules (3 rings x 12 segments)
    
    # Iridology Mappings Dictionary
    mappings = {
        # Ring 1: Inner (Stomach/Digestive Core)
        "ring_1_segment_1": ("Stomach Fundus", "redness > 0.6", "Gastric inflammation", "High redness in the superior inner ring indicates potential stomach irritation.", "medium"),
        "ring_1_segment_2": ("Upper Digestion", "spots.has_spots == true", "Gastric toxicity", "Pigmentation suggests slow upper digestive transit.", "high"),
        "ring_1_segment_3": ("Pylorus", "roughness > 0.5", "Pyloric tension", "Rough texture indicates potential spasms or tension in the pyloric region.", "low"),
        "ring_1_segment_4": ("Duodenum", "brightness < 0.3", "Duodenal sluggishness", "Darkness in this zone suggests underactive duodenal function.", "medium"),
        "ring_1_segment_5": ("Jejunum", "cracks.density > 0.3", "Small intestine laxity", "Cracks imply weakened small intestinal walls.", "medium"),
        "ring_1_segment_6": ("Ileum", "redness > 0.5", "Ileal inflammation", "Redness suggests acute irritation in the lower small intestine.", "medium"),
        "ring_1_segment_7": ("Cecum", "spots.has_spots == true", "Cecal congestion", "Dark spots indicate potential stagnation in the cecum.", "high"),
        "ring_1_segment_8": ("Ascending Colon", "uniformity < 0.4", "Colon irregularity", "Low uniformity suggests irregular peristalsis.", "medium"),
        "ring_1_segment_9": ("Transverse Colon", "roughness > 0.6", "Transverse colon tension", "Rough texture indicates spasticity or tension in the transverse colon.", "medium"),
        "ring_1_segment_10": ("Descending Colon", "cracks.density > 0.5", "Bowel wall weakness", "High crack density indicates potential diverticular weakness.", "high"),
        "ring_1_segment_11": ("Sigmoid Colon", "brightness < 0.2", "Sigmoid sluggishness", "Extreme darkness suggests poor elimination or constipation.", "high"),
        "ring_1_segment_12": ("Rectum", "redness > 0.5", "Rectal irritation", "Redness correlates with potential hemorrhoids or local irritation.", "low"),

        # Ring 2: Middle (Autonomic Nervous System / Muscles)
        "ring_2_segment_1": ("Brain/ANS", "redness > 0.6", "Cephalic ANS stress", "Redness in the superior middle ring correlates with mental stress or anxiety.", "medium"),
        "ring_2_segment_2": ("Facial Nerves", "cracks.density > 0.3", "Facial nerve tension", "Fissures indicate potential tension in facial or trigeminal nerves.", "low"),
        "ring_2_segment_3": ("Upper Spine", "roughness > 0.5", "Cervical spine stress", "Roughness correlates with muscle tension in the neck/cervical region.", "medium"),
        "ring_2_segment_4": ("Upper Back Muscles", "spots.has_spots == true", "Thoracic muscle toxicity", "Spots indicate potential buildup of lactic acid or tension in upper back.", "medium"),
        "ring_2_segment_5": ("Lower Back Muscles", "brightness < 0.4", "Lumbar fatigue", "Darkness suggests chronic fatigue or weakness in lumbar muscles.", "low"),
        "ring_2_segment_6": ("Pelvic Nerves", "redness > 0.5", "Pelvic nerve irritation", "Redness indicates acute irritation in the pelvic floor or sciatic pathway.", "medium"),
        "ring_2_segment_7": ("Leg Muscles", "cracks.density > 0.4", "Lower limb weakness", "Cracks suggest poor circulation or muscle weakness in the legs.", "low"),
        "ring_2_segment_8": ("Abdominal Muscles", "roughness > 0.6", "Core tension", "Rough texture indicates tension or cramping in abdominal muscles.", "medium"),
        "ring_2_segment_9": ("Chest Muscles", "uniformity < 0.3", "Pectoral tightness", "Irregularity suggests restricted movement or tension in the chest.", "low"),
        "ring_2_segment_10": ("Shoulder Muscles", "spots.has_spots == true", "Shoulder joint stress", "Pigmentation correlates with chronic stress or calcification in shoulders.", "medium"),
        "ring_2_segment_11": ("Arm Nerves", "redness > 0.5", "Brachial plexus irritation", "Redness suggests acute nerve irritation extending to the arms.", "medium"),
        "ring_2_segment_12": ("Neck Muscles", "cracks.density > 0.5", "Severe neck tension", "High fissure density indicates chronic stiffness or structural tension in the neck.", "high"),

        # Ring 3: Outer (Organs / Glands / Peripheral)
        "ring_3_segment_1": ("Brain/Cerebrum", "brightness < 0.3", "Cerebral fatigue", "Darkness in the top outer ring suggests mental exhaustion or poor cerebral circulation.", "high"),
        "ring_3_segment_2": ("Face/Sinuses", "redness > 0.6", "Sinus inflammation", "Redness correlates with acute sinus congestion or allergies.", "medium"),
        "ring_3_segment_3": ("Throat/Trachea", "roughness > 0.5", "Throat irritation", "Rough texture suggests potential pharyngitis or vocal cord strain.", "low"),
        "ring_3_segment_4": ("Lungs/Pleura", "cracks.density > 0.4", "Respiratory laxity", "Cracks in the lateral outer ring indicate weakened respiratory function.", "medium"),
        "ring_3_segment_5": ("Heart/Liver", "spots.has_spots == true", "Cardiovascular/Hepatic toxicity", "Spots suggest toxic buildup or sluggishness in major metabolic organs.", "high"),
        "ring_3_segment_6": ("Kidneys/Adrenals", "brightness < 0.2", "Adrenal exhaustion", "Severe darkness at the 6 o'clock position strongly correlates with chronic adrenal fatigue.", "high"),
        "ring_3_segment_7": ("Ovaries/Testes", "redness > 0.5", "Reproductive inflammation", "Redness suggests acute irritation or hormonal imbalance in reproductive organs.", "medium"),
        "ring_3_segment_8": ("Pelvis/Hip", "roughness > 0.6", "Hip joint stress", "Roughness indicates potential arthritis or structural stress in the hips.", "low"),
        "ring_3_segment_9": ("Spleen", "uniformity < 0.3", "Lymphatic congestion", "Irregularity correlates with poor lymphatic drainage or splenic stress.", "medium"),
        "ring_3_segment_10": ("Ribs/Breast", "spots.has_spots == true", "Mammary/Thoracic congestion", "Pigmentation suggests localized congestion or benign fibrocystic tendencies.", "low"),
        "ring_3_segment_11": ("Neck/Thyroid", "cracks.density > 0.5", "Thyroid weakness", "Cracks suggest potential hypothyroidism or metabolic imbalance.", "high"),
        "ring_3_segment_12": ("Eye/Ear", "redness > 0.5", "Sensory organ irritation", "Redness indicates acute strain or infection in the eyes or ears.", "medium"),
    }
    
    # Get existing regions to avoid duplicate creation errors
    regions_res = requests.get(f"{BASE_URL}/zone-regions?zone_map_id={map_id}")
    existing_regions = {r["name"]: r["id"] for r in regions_res.json().get("data", {}).get("items", [])}
    
    for region_name, (zone_desc, condition, finding, desc, severity) in mappings.items():
        if region_name not in existing_regions:
            res = requests.post(f"{BASE_URL}/zone-regions", json={
                "zone_map_id": map_id,
                "name": region_name,
                "coordinates": "[]"
            })
            if res.status_code in (200, 201):
                region_id = res.json().get("data", {}).get("id") or res.json().get("id")
                existing_regions[region_name] = region_id
            else:
                print(f"Failed to create region {region_name}: {res.text}")
                continue
        else:
            region_id = existing_regions[region_name]
            
        # Create the rule
        res = requests.post(f"{BASE_URL}/rules", json={
            "zone_region_id": region_id,
            "scan_type": "iris",
            "condition": condition,
            "finding": f"[{zone_desc}] {finding}",
            "description": desc,
            "severity": severity
        })
        if res.status_code in (200, 201):
            print(f"Created rule for {region_name}: {finding}")
        else:
            print(f"Failed to create rule for {region_name}: {res.text}")

if __name__ == "__main__":
    seed_all_iris_rules()
