import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Optional
import math

class GeoAnalyzer:
    def __init__(self):
        self.known_locations = {}
    
    def extract_gps_from_image(self, image_path: str) -> Optional[Dict]:
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            
            if not exif_data:
                return None
            
            gps_info = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = value[gps_tag_id]
            
            if not gps_info:
                return None
            
            lat = self._convert_to_degrees(gps_info.get("GPSLatitude"))
            lat_ref = gps_info.get("GPSLatitudeRef", "N")
            lon = self._convert_to_degrees(gps_info.get("GPSLongitude"))
            lon_ref = gps_info.get("GPSLongitudeRef", "E")
            
            if lat is not None and lon is not None:
                if lat_ref == "S":
                    lat = -lat
                if lon_ref == "W":
                    lon = -lon
                
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "has_gps": True,
                    "raw_gps": {k: str(v) for k, v in gps_info.items()}
                }
        
        except Exception as e:
            return {"error": str(e), "has_gps": False}
        
        return {"has_gps": False}
    
    def _convert_to_degrees(self, value) -> Optional[float]:
        if value is None:
            return None
        
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except (TypeError, IndexError, ValueError):
            return None
    
    def estimate_location_from_context(self, image_path: str, complaint_text: str = "") -> Dict:
        result = {
            "estimated_location": None,
            "location_type": "unknown",
            "confidence": 0.0,
            "context_clues": []
        }
        
        gps_data = self.extract_gps_from_image(image_path)
        if gps_data and gps_data.get("has_gps"):
            result["estimated_location"] = {
                "latitude": gps_data["latitude"],
                "longitude": gps_data["longitude"]
            }
            result["location_type"] = "gps_exact"
            result["confidence"] = 1.0
            return result
        
        location_keywords = self._extract_location_keywords(complaint_text)
        if location_keywords:
            result["context_clues"] = location_keywords
            result["location_type"] = "text_context"
            result["confidence"] = 0.5
        
        img = cv2.imread(image_path)
        if img is not None:
            visual_clues = self._analyze_visual_context(img)
            result["context_clues"].extend(visual_clues)
            if visual_clues:
                result["confidence"] = max(result["confidence"], 0.3)
        
        return result
    
    def _extract_location_keywords(self, text: str) -> list:
        keywords = []
        
        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
            "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
            "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]
        
        common_cities = [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
            "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
            "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara",
            "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut"
        ]
        
        text_lower = text.lower()
        
        for state in indian_states:
            if state.lower() in text_lower:
                keywords.append({"type": "state", "value": state})
        
        for city in common_cities:
            if city.lower() in text_lower:
                keywords.append({"type": "city", "value": city})
        
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["village", "town", "city", "district", "area", "locality", "ward", "sector", "colony"]:
                if i > 0:
                    keywords.append({"type": "area_name", "value": words[i-1]})
        
        return keywords
    
    def _analyze_visual_context(self, img: np.ndarray) -> list:
        clues = []
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        green_mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
        green_ratio = np.sum(green_mask > 0) / green_mask.size
        
        if green_ratio > 0.3:
            clues.append({"type": "environment", "value": "rural/green_area"})
        elif green_ratio < 0.1:
            clues.append({"type": "environment", "value": "urban/built_area"})
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        if edge_density > 0.15:
            clues.append({"type": "structure", "value": "dense_buildings"})
        elif edge_density < 0.05:
            clues.append({"type": "structure", "value": "open_area"})
        
        return clues
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def find_nearest_resources(self, lat: float, lon: float, resources: list, radius_km: float = 50) -> list:
        nearby = []
        
        for resource in resources:
            if resource.get("latitude") and resource.get("longitude"):
                distance = self.calculate_distance(
                    lat, lon,
                    resource["latitude"], resource["longitude"]
                )
                if distance <= radius_km:
                    nearby.append({
                        **resource,
                        "distance_km": round(distance, 2)
                    })
        
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby
