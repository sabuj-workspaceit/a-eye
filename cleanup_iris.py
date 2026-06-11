import requests

BASE_URL = "http://localhost:8000/api/v1/practitioner"

def cleanup():
    # Delete all rules for iris
    rules_res = requests.get(f"{BASE_URL}/rules?scan_type=iris")
    for r in rules_res.json().get("data", {}).get("items", []):
        requests.delete(f"{BASE_URL}/rules/{r['id']}")
    
    # Delete all zone-regions for map_id=4 (Iris)
    # wait, map might not be 4, let's fetch map_id
    maps_res = requests.get(f"{BASE_URL}/zone-maps?scan_type=iris")
    maps = maps_res.json().get("data", {}).get("items", [])
    if maps:
        map_id = maps[0]["id"]
        regions_res = requests.get(f"{BASE_URL}/zone-regions?zone_map_id={map_id}")
        for r in regions_res.json().get("data", {}).get("items", []):
            requests.delete(f"{BASE_URL}/zone-regions/{r['id']}")
    print("Cleaned up!")

if __name__ == "__main__":
    cleanup()
