import requests

BASE_URL = "http://localhost:8000/api/v1/practitioner"

def seed_iris_rules():
    print("Seeding Iris Rules...")
    
    # 1. Create or get ZoneMap
    maps_res = requests.get(f"{BASE_URL}/zone-maps?scan_type=iris")
    maps = maps_res.json().get("data", {}).get("items", [])
    
    if not maps:
        res = requests.post(f"{BASE_URL}/zone-maps", json={
            "name": "Iris Standard Map",
            "scan_type": "iris"
        })
        if res.status_code != 200:
            print("Failed to create ZoneMap:", res.text)
            return
        map_id = res.json().get("id") or res.json().get("data", {}).get("id")
    else:
        map_id = maps[0]["id"]
        
    print(f"ZoneMap ID: {map_id}")
    
    # 2. Define Regions and Rules to create
    rules_to_create = [
        {
            "region_name": "ring_1_segment_1", # Top Inner (Head/Brain)
            "condition": "redness > 0.6",
            "finding": "Inflammatory indicators in Head/Brain zone",
            "description": "Elevated redness in the superior inner ring may correlate with cephalic stress or tension headaches.",
            "severity": "medium"
        },
        {
            "region_name": "ring_2_segment_6", # Bottom Middle (Digestive/Abdomen)
            "condition": "spots.has_spots == true",
            "finding": "Pigmentation in Digestive zone",
            "description": "Presence of localized pigmentation may suggest chronic sluggishness or toxicity in the gastrointestinal tract.",
            "severity": "high"
        },
        {
            "region_name": "ring_3_segment_9", # Right Outer (Lung/Thorax)
            "condition": "cracks.density > 0.4",
            "finding": "Structural laxity in Thoracic zone",
            "description": "High fissure density in the lateral outer ring may indicate respiratory weakness or reduced bronchial vitality.",
            "severity": "low"
        }
    ]
    
    # Get existing regions to avoid duplicate creation errors
    regions_res = requests.get(f"{BASE_URL}/zone-regions?zone_map_id={map_id}")
    existing_regions = {r["name"]: r["id"] for r in regions_res.json().get("data", {}).get("items", [])}
    
    for rt in rules_to_create:
        region_name = rt["region_name"]
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
            "condition": rt["condition"],
            "finding": rt["finding"],
            "description": rt["description"],
            "severity": rt["severity"]
        })
        if res.status_code in (200, 201):
            print(f"Successfully created rule for {region_name}")
        else:
            print(f"Failed to create rule for {region_name}: {res.text}")

if __name__ == "__main__":
    seed_iris_rules()
