import json
import logging
from app.db.base import SessionLocal
from app.db.models.zone_map import ZoneMap
from app.db.models.zone_region import ZoneRegion
from app.db.models.rule import Rule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

def seed_data():
    db = SessionLocal()
    try:
        logger.info("Starting database seeding...")
        
        # 1. Clear existing seed-related records to avoid duplicates
        logger.info("Cleaning up existing rules, zone regions, and zone maps...")
        db.query(Rule).delete()
        db.query(ZoneRegion).delete()
        db.query(ZoneMap).delete()
        db.commit()

        # Define default maps and zones
        # Note: Zoning service defines specific coordinates based on width/height.
        # Here we seed dummy coordinates that will be matched by default logic.
        zone_definitions = {
            "eye": {
                "name": "eye_default",
                "description": "Default practitioner map for iris and eye analysis",
                "zones": [
                    {
                        "name": "center",
                        "coordinates": json.dumps([0.25, 0.25, 0.75, 0.75]),
                        "description": "Central iris region",
                        "rules": [
                            {
                                "condition": "redness > 0.05",
                                "description": "Elevated redness detected in iris center, indicating possible local congestion or heat pattern.",
                                "severity": "medium",
                            },
                            {
                                "condition": "brightness < 80",
                                "description": "Low brightness in central iris, indicating low vitality or energy stagnation.",
                                "severity": "low",
                            },
                            {
                                "condition": "texture > 15",
                                "description": "High texture complexity in central iris, indicating structural density shifts.",
                                "severity": "medium",
                            }
                        ]
                    }
                ]
            },
            "tongue": {
                "name": "tongue_default",
                "description": "Default practitioner map for tongue analysis",
                "zones": [
                    {
                        "name": "bottom_right",
                        "coordinates": json.dumps([0.5, 0.5, 1.0, 1.0]),
                        "description": "Lower right quadrant of the tongue",
                        "rules": [
                            {
                                "condition": "redness > 0.05",
                                "description": "Increased redness in bottom right tongue zone, suggesting heat pattern or digestive stress.",
                                "severity": "medium",
                            },
                            {
                                "condition": "texture > 10",
                                "description": "Slightly rough tongue texture, suggesting potential coating or structural variations.",
                                "severity": "low",
                            }
                        ]
                    }
                ]
            },
            "face": {
                "name": "face_default",
                "description": "Default practitioner map for facial wellness analysis",
                "zones": [
                    {
                        "name": "top_left",
                        "coordinates": json.dumps([0, 0, 0.5, 0.5]),
                        "description": "Top left forehead region",
                        "rules": [
                            {
                                "condition": "redness > 0.08",
                                "description": "Significant redness detected in forehead region, suggesting possible irritation or stress.",
                                "severity": "medium",
                            },
                            {
                                "condition": "brightness > 200",
                                "description": "High brightness in top left facial zone, suggesting potential excess skin oil or reflection.",
                                "severity": "low",
                            }
                        ]
                    }
                ]
            }
        }

        # Seed each scan type
        for scan_type, map_info in zone_definitions.items():
            # Create ZoneMap
            zone_map = ZoneMap(
                name=map_info["name"],
                scan_type=scan_type,
                description=map_info["description"]
            )
            db.add(zone_map)
            db.commit()
            db.refresh(zone_map)
            logger.info(f"Created ZoneMap: {zone_map.name} for {scan_type}")

            for zone_info in map_info["zones"]:
                # Create ZoneRegion
                zone_region = ZoneRegion(
                    zone_map_id=zone_map.id,
                    name=zone_info["name"],
                    coordinates=zone_info["coordinates"],
                    description=zone_info["description"]
                )
                db.add(zone_region)
                db.commit()
                db.refresh(zone_region)
                logger.info(f"  Created ZoneRegion: {zone_region.name}")

                for rule_info in zone_info["rules"]:
                    # Create Rule
                    rule = Rule(
                        zone_region_id=zone_region.id,
                        scan_type=scan_type,
                        condition=rule_info["condition"],
                        description=rule_info["description"],
                        severity=rule_info["severity"]
                    )
                    db.add(rule)
                    logger.info(f"    Created Rule: {rule.condition} -> {rule.description[:40]}...")
            
            db.commit()

        logger.info("Database seeding completed successfully!")
    except Exception as exc:
        db.rollback()
        logger.error(f"Seeding failed: {exc}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
