import re
from typing import Dict, List
from collections import Counter

class ToneAnalyzer:
    def __init__(self):
        self.emergency_keywords = {
            "critical": {
                "keywords": ["urgent", "emergency", "danger", "death", "dying", "critical", "immediate", "life-threatening", "casualty", "trapped", "collapsed", "fire", "explosion", "flood rising", "bridge collapse", "building collapse"],
                "weight": 5.0,
                "level": 5
            },
            "high": {
                "keywords": ["severe", "serious", "flooded", "destroyed", "damaged badly", "injured", "stuck", "blocked", "no water", "no electricity", "gas leak", "structural damage", "crack spreading"],
                "weight": 4.0,
                "level": 4
            },
            "medium": {
                "keywords": ["broken", "damaged", "pothole", "crack", "leaking", "overflow", "stagnant water", "garbage", "clogged", "damaged road", "fallen tree", "power outage"],
                "weight": 3.0,
                "level": 3
            },
            "low": {
                "keywords": ["minor", "small", "scratch", "slight", "cosmetic", "surface", "light damage", "paint peeling", "minor crack"],
                "weight": 2.0,
                "level": 2
            },
            "info": {
                "keywords": ["request", "suggestion", "improvement", "maintenance", "routine", "check", "inspect", "clean", "trim"],
                "weight": 1.0,
                "level": 1
            }
        }
        
        self.urgency_words = ["now", "immediately", "asap", "hurry", "fast", "quick", "today", "tonight", "right now", "cannot wait"]
        self.emotional_words = ["dangerous", "scared", "afraid", "terrible", "horrible", "disaster", "help", "please help", "someone help"]
        self.vulnerable_words = ["children", "babies", "kids", "elderly", "old people", "disabled", "pregnant", "sick", "hospital", "school"]
    
    def analyze(self, text: str) -> Dict:
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        category = self._determine_category(text_lower)
        
        emergency_level = self._calculate_emergency_level(text_lower, words)
        
        urgency_score = self._calculate_urgency(text_lower)
        
        vulnerability_score = self._calculate_vulnerability(text_lower)
        
        emotional_score = self._calculate_emotional_intensity(text_lower)
        
        danger_score = self._calculate_danger_score(
            emergency_level, urgency_score, vulnerability_score, emotional_score
        )
        
        infrastructure_type = self._detect_infrastructure_type(text_lower)
        
        has_children = any(word in text_lower for word in self.vulnerable_words)
        
        return {
            "category": category,
            "emergency_level": emergency_level,
            "danger_score": round(danger_score, 2),
            "urgency_score": round(urgency_score, 2),
            "vulnerability_score": round(vulnerability_score, 2),
            "emotional_score": round(emotional_score, 2),
            "has_children_vulnerability": has_children,
            "infrastructure_type": infrastructure_type,
            "risk_factors": self._identify_risk_factors(text_lower),
            "recommended_priority": self._get_priority_recommendation(danger_score, has_children)
        }
    
    def _determine_category(self, text: str) -> str:
        categories = {
            "road": ["road", "pothole", "street", "highway", "path", "driveway", "asphalt", "pavement", "sidewalk"],
            "water": ["water", "pipe", "drainage", "sewage", "flood", "leak", "tap", "well", "pipeline", "water supply", "drain"],
            "electricity": ["electricity", "power", "wire", "pole", "transformer", "outage", "blackout", "electrical"],
            "building": ["building", "wall", "roof", "structure", "house", "collapse", "crack", "foundation", "plaster"],
            "sanitation": ["garbage", "waste", "trash", "dustbin", "cleaning", "sanitation", "latrine", "toilet"],
            "bridge": ["bridge", "overpass", "flyover", "underpass"],
            "tree": ["tree", "fallen", "branch", "vegetation", "overgrown"],
            "fire": ["fire", "burn", "smoke", "blaze"],
            "other": []
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "other"
    
    def _calculate_emergency_level(self, text: str, words: list) -> int:
        max_level = 0
        
        for level_name, level_data in self.emergency_keywords.items():
            for keyword in level_data["keywords"]:
                if keyword in text:
                    max_level = max(max_level, level_data["level"])
        
        return max_level
    
    def _calculate_urgency(self, text: str) -> float:
        score = 0
        for word in self.urgency_words:
            if word in text:
                score += 0.2
        return min(1.0, score)
    
    def _calculate_vulnerability(self, text: str) -> float:
        score = 0
        for word in self.vulnerable_words:
            if word in text:
                score += 0.3
        return min(1.0, score)
    
    def _calculate_emotional_intensity(self, text: str) -> float:
        score = 0
        for word in self.emotional_words:
            if word in text:
                score += 0.2
        
        exclamation_count = text.count('!')
        if exclamation_count > 3:
            score += 0.3
        elif exclamation_count > 1:
            score += 0.1
        
        caps_words = len(re.findall(r'\b[A-Z]{2,}\b', text))
        score += min(0.3, caps_words * 0.1)
        
        return min(1.0, score)
    
    def _calculate_danger_score(self, emergency: int, urgency: float, vulnerability: float, emotional: float) -> float:
        emergency_normalized = emergency / 5.0
        
        danger = (
            emergency_normalized * 0.4 +
            urgency * 0.25 +
            vulnerability * 0.2 +
            emotional * 0.15
        )
        
        return min(1.0, danger)
    
    def _detect_infrastructure_type(self, text: str) -> str:
        types = {
            "pothole": ["pothole", "pit", "hole in road"],
            "crack": ["crack", "cracking", "split"],
            "flood": ["flood", "flooding", "waterlogged", "submerged"],
            "leak": ["leak", "leaking", "dripping", "burst pipe"],
            "collapse": ["collapse", "collapsed", "fallen", "caved in"],
            "electrical_hazard": ["live wire", "exposed wire", "sparking", "electric shock"],
            "fire_hazard": ["fire", "smoke", "burning", "blaze"],
            "garbage": ["garbage", "waste", "trash", "dump"],
            "blocked_drain": ["blocked drain", "clogged drain", "overflowing drain"]
        }
        
        for dtype, keywords in types.items():
            if any(keyword in text for keyword in keywords):
                return dtype
        
        return "general"
    
    def _identify_risk_factors(self, text: str) -> list:
        factors = []
        
        if any(word in text for word in self.vulnerable_words):
            factors.append("vulnerable_population")
        
        if any(word in text for word in ["school", "hospital", "temple", "mosque", "church"]):
            factors.append("public_facility")
        
        if any(word in text for word in ["main road", "highway", "busy", "traffic"]):
            factors.append("high_traffic_area")
        
        if any(word in text for word in ["night", "dark", "no light"]):
            factors.append("low_visibility")
        
        if any(word in text for word in ["rain", "monsoon", "heavy rain", "storm"]):
            factors.append("weather_aggravation")
        
        return factors
    
    def _get_priority_recommendation(self, danger_score: float, has_children: bool) -> str:
        if danger_score > 0.8 or has_children:
            return "immediate"
        elif danger_score > 0.6:
            return "urgent"
        elif danger_score > 0.4:
            return "high"
        elif danger_score > 0.2:
            return "medium"
        else:
            return "low"
