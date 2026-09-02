import sqlite3
from typing import Dict, List
from datetime import datetime

class PriorityEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def calculate_priority(self, complaint_data: Dict, tone_analysis: Dict, 
                          damage_analysis: Dict, geo_data: Dict) -> Dict:
        
        danger_score = tone_analysis.get("danger_score", 0)
        emergency_level = tone_analysis.get("emergency_level", 0)
        has_children = tone_analysis.get("has_children_vulnerability", False)
        
        damage_severity = damage_analysis.get("overall_severity", 0) if damage_analysis else 0
        total_damages = damage_analysis.get("total_damages", 0) if damage_analysis else 0
        
        city_resources = self._get_city_resources(geo_data)
        
        resource_factor = self._calculate_resource_factor(city_resources)
        
        base_score = danger_score * 0.35
        
        damage_factor = damage_severity * 0.25
        
        emergency_factor = (emergency_level / 5.0) * 0.2
        
        vulnerability_factor = 0.15 if has_children else 0
        
        resource_adjustment = resource_factor * 0.05
        
        final_score = base_score + damage_factor + emergency_factor + vulnerability_factor - resource_adjustment
        
        final_score = max(0, min(1.0, final_score))
        
        priority_tier = self._get_priority_tier(final_score, emergency_level, has_children)
        
        zone_classification = self._classify_zone(final_score, damage_severity, emergency_level)
        
        assigned_official = self._find_best_official(
            complaint_data.get("category"),
            geo_data,
            city_resources
        )
        
        sms_targets = self._get_sms_targets(complaint_data.get("category"), geo_data)
        
        return {
            "final_score": round(final_score, 3),
            "priority_tier": priority_tier,
            "zone_classification": zone_classification,
            "components": {
                "danger_base": round(base_score, 3),
                "damage_factor": round(damage_factor, 3),
                "emergency_factor": round(emergency_factor, 3),
                "vulnerability_factor": round(vulnerability_factor, 3),
                "resource_adjustment": round(resource_adjustment, 3)
            },
            "assigned_official": assigned_official,
            "sms_targets": sms_targets,
            "city_resources": city_resources,
            "justification": self._generate_justification(
                danger_score, damage_severity, emergency_level, 
                has_children, resource_factor, assigned_official
            )
        }
    
    def _get_city_resources(self, geo_data: Dict) -> Dict:
        city = geo_data.get("city", "unknown")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM city_resources WHERE city = ? ORDER BY last_updated DESC LIMIT 1",
            (city,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        
        return {
            "city": city,
            "available_workers": 0,
            "available_vehicles": 0,
            "emergency_capacity": "unknown"
        }
    
    def _calculate_resource_factor(self, city_resources: Dict) -> float:
        workers = city_resources.get("available_workers", 0)
        vehicles = city_resources.get("available_vehicles", 0)
        
        capacity = city_resources.get("emergency_capacity", "normal")
        
        capacity_scores = {
            "overwhelmed": 0.0,
            "strained": 0.3,
            "normal": 0.5,
            "available": 0.8,
            "unknown": 0.5
        }
        
        worker_score = min(1.0, workers / 50) if workers > 0 else 0.2
        vehicle_score = min(1.0, vehicles / 10) if vehicles > 0 else 0.2
        capacity_score = capacity_scores.get(capacity, 0.5)
        
        return (worker_score + vehicle_score + capacity_score) / 3
    
    def _get_priority_tier(self, score: float, emergency_level: int, has_children: bool) -> str:
        if score > 0.8 or emergency_level >= 5:
            return "critical"
        elif score > 0.6 or emergency_level >= 4 or has_children:
            return "urgent"
        elif score > 0.4 or emergency_level >= 3:
            return "high"
        elif score > 0.2:
            return "medium"
        else:
            return "low"
    
    def _classify_zone(self, final_score: float, damage_severity: float, emergency_level: int) -> str:
        if final_score > 0.7 or emergency_level >= 5:
            return "danger_zone_critical"
        elif final_score > 0.5 or damage_severity > 0.6:
            return "danger_zone_high"
        elif final_score > 0.3:
            return "danger_zone_moderate"
        else:
            return "danger_zone_low"
    
    def _find_best_official(self, category: str, geo_data: Dict, city_resources: Dict) -> Dict:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        department_map = {
            "road": "public_works",
            "water": "water_supply",
            "electricity": "electricity",
            "building": "municipal",
            "sanitation": "sanitation",
            "bridge": "public_works",
            "tree": "forest",
            "fire": "fire_services"
        }
        
        department = department_map.get(category, "general")
        city = geo_data.get("city", "")
        village = geo_data.get("village", "")
        
        cursor.execute("""
            SELECT * FROM officials 
            WHERE department = ? AND is_active = 1
            AND (city = ? OR village = ? OR city = '' OR city IS NULL)
            ORDER BY 
                CASE WHEN city = ? THEN 0
                     WHEN village = ? THEN 1
                     ELSE 2 END
            LIMIT 1
        """, (department, city, village, city, village))
        
        official = cursor.fetchone()
        
        if not official:
            cursor.execute("""
                SELECT * FROM officials 
                WHERE is_active = 1
                ORDER BY 
                    CASE WHEN department = ? THEN 0 ELSE 1 END
                LIMIT 1
            """, (department,))
            official = cursor.fetchone()
        
        conn.close()
        
        if official:
            return {
                "name": official["name"],
                "role": official["role"],
                "phone": official["phone"],
                "department": official["department"],
                "city": official["city"],
                "village": official["village"]
            }
        
        return {
            "name": "Auto-assigned",
            "role": "Field Officer",
            "phone": "",
            "department": department,
            "city": city,
            "village": village,
            "note": "No specific official found - needs manual assignment"
        }
    
    def _get_sms_targets(self, category: str, geo_data: Dict) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        department_map = {
            "road": "public_works",
            "water": "water_supply",
            "electricity": "electricity",
            "building": "municipal",
            "sanitation": "sanitation",
            "bridge": "public_works",
            "tree": "forest",
            "fire": "fire_services"
        }
        
        department = department_map.get(category, "general")
        city = geo_data.get("city", "")
        village = geo_data.get("village", "")
        
        cursor.execute("""
            SELECT * FROM officials 
            WHERE department = ? AND is_active = 1
            AND (city = ? OR village = ? OR city = '' OR city IS NULL)
        """, (department, city, village))
        
        officials = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM officials 
            WHERE role IN ('district_magistrate', 'collector', 'deo')
            AND is_active = 1
            AND (city = ? OR city = '' OR city IS NULL)
            LIMIT 2
        """, (city,))
        
        superiors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        targets = []
        for official in officials:
            targets.append({
                "name": official["name"],
                "phone": official["phone"],
                "role": official["role"],
                "reason": f"Primary contact for {department} department"
            })
        
        for superior in superiors:
            targets.append({
                "name": superior["name"],
                "phone": superior["phone"],
                "role": superior["role"],
                "reason": f"Administrative oversight"
            })
        
        return targets
    
    def _generate_justification(self, danger_score, damage_severity, emergency_level,
                                has_children, resource_factor, official) -> str:
        reasons = []
        
        if danger_score > 0.7:
            reasons.append(f"High danger score ({danger_score:.2f})")
        if emergency_level >= 4:
            reasons.append(f"Emergency level {emergency_level}/5")
        if has_children:
            reasons.append("Vulnerable population (children) at risk")
        if damage_severity > 0.6:
            reasons.append(f"Severe infrastructure damage ({damage_severity:.2f})")
        if resource_factor < 0.3:
            reasons.append("Limited local resources - needs external support")
        
        if not reasons:
            reasons.append("Standard priority based on complaint analysis")
        
        return "; ".join(reasons)
