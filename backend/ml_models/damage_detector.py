import cv2
import numpy as np
from PIL import Image
import os
from typing import Dict, List, Tuple

class DamageDetector:
    def __init__(self):
        self.damage_types = {
            "scratch": {"min_area": 100, "color_range": (0, 50)},
            "pothole": {"min_area": 500, "color_range": (0, 80)},
            "crack": {"min_area": 200, "color_range": (0, 60)},
            "flood": {"min_area": 1000, "color_range": (80, 130)},
            "debris": {"min_area": 300, "color_range": (0, 255)},
        }
    
    def analyze_image(self, image_path: str) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not load image"}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        damages = []
        
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        pothole_damages = self._detect_potholes(gray, img)
        scratch_damages = self._detect_scratches(gray, img)
        crack_damages = self._detect_cracks(edges, img)
        flood_damages = self._detect_floods(hsv, img)
        debris_damages = self._detect_debris(img)
        
        damages.extend(pothole_damages)
        damages.extend(scratch_damages)
        damages.extend(crack_damages)
        damages.extend(flood_damages)
        damages.extend(debris_damages)
        
        overall_severity = self._calculate_severity(damages, img.shape)
        
        return {
            "damages": damages,
            "overall_severity": overall_severity,
            "image_dimensions": img.shape[:2],
            "total_damages": len(damages),
            "damage_summary": self._summarize_damages(damages)
        }
    
    def _detect_potholes(self, gray: np.ndarray, img: np.ndarray) -> List[Dict]:
        damages = []
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY_INV)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                circularity = 4 * np.pi * area / (cv2.arcLength(contour, True) ** 2 + 1)
                
                if circularity > 0.3:
                    severity = min(1.0, area / 5000)
                    damages.append({
                        "type": "pothole",
                        "severity": severity,
                        "area": int(area),
                        "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                        "circularity": float(circularity),
                        "description": f"Pothole detected ({w}x{h}px, severity: {severity:.2f})"
                    })
        return damages
    
    def _detect_scratches(self, gray: np.ndarray, img: np.ndarray) -> List[Dict]:
        damages = []
        edges = cv2.Canny(gray, 100, 200)
        
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
        
        if lines is not None:
            scratch_groups = self._group_lines(lines)
            
            for group in scratch_groups:
                if len(group) >= 2:
                    all_points = np.array([pt for line in group for pt in line])
                    x, y, w, h = cv2.boundingRect(all_points)
                    length = np.sqrt(w**2 + h**2)
                    
                    if length > 30:
                        severity = min(1.0, length / 200)
                        damages.append({
                            "type": "scratch",
                            "severity": severity,
                            "length": float(length),
                            "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                            "description": f"Scratch detected (length: {length:.0f}px, severity: {severity:.2f})"
                        })
        return damages
    
    def _detect_cracks(self, edges: np.ndarray, img: np.ndarray) -> List[Dict]:
        damages = []
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / (h + 1)
            
            if 50 < area < 5000 and (aspect_ratio > 3 or aspect_ratio < 0.33):
                severity = min(1.0, area / 2000)
                damages.append({
                    "type": "crack",
                    "severity": severity,
                    "area": int(area),
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "aspect_ratio": float(aspect_ratio),
                    "description": f"Crack detected ({w}x{h}px, severity: {severity:.2f})"
                })
        return damages
    
    def _detect_floods(self, hsv: np.ndarray, img: np.ndarray) -> List[Dict]:
        damages = []
        lower_blue = np.array([85, 50, 50])
        upper_blue = np.array([135, 255, 255])
        
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                severity = min(1.0, area / 10000)
                damages.append({
                    "type": "flood",
                    "severity": severity,
                    "area": int(area),
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "description": f"Water/flood detected ({w}x{h}px, severity: {severity:.2f})"
                })
        return damages
    
    def _detect_debris(self, img: np.ndarray) -> List[Dict]:
        damages = []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:
                x, y, w, h = cv2.boundingRect(contour)
                severity = min(1.0, area / 2000)
                damages.append({
                    "type": "debris",
                    "severity": severity,
                    "area": int(area),
                    "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "description": f"Debris detected ({w}x{h}px, severity: {severity:.2f})"
                })
        return damages
    
    def _group_lines(self, lines: np.ndarray, threshold: float = 30) -> List[List]:
        groups = []
        used = set()
        
        for i, line1 in enumerate(lines):
            if i in used:
                continue
            group = [line1[0]]
            used.add(i)
            
            for j, line2 in enumerate(lines):
                if j in used:
                    continue
                dist = self._line_distance(line1[0], line2[0])
                if dist < threshold:
                    group.append(line2[0])
                    used.add(j)
            
            groups.append(group)
        return groups
    
    def _line_distance(self, line1, line2) -> float:
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
        mid1 = ((x1+x2)/2, (y1+y2)/2)
        mid2 = ((x3+x4)/2, (y3+y4)/2)
        return np.sqrt((mid1[0]-mid2[0])**2 + (mid1[1]-mid2[1])**2)
    
    def _calculate_severity(self, damages: List[Dict], image_shape: Tuple) -> float:
        if not damages:
            return 0.0
        
        total_area = image_shape[0] * image_shape[1]
        weighted_severity = 0
        total_weight = 0
        
        severity_weights = {
            "pothole": 1.5,
            "crack": 1.2,
            "flood": 2.0,
            "scratch": 0.8,
            "debris": 1.0
        }
        
        for damage in damages:
            weight = severity_weights.get(damage["type"], 1.0)
            damage_area = damage.get("area", 0) / total_area
            weighted_severity += damage["severity"] * weight * (1 + damage_area * 10)
            total_weight += weight
        
        return min(1.0, weighted_severity / max(total_weight, 1))
    
    def _summarize_damages(self, damages: List[Dict]) -> Dict:
        summary = {}
        for damage in damages:
            dtype = damage["type"]
            if dtype not in summary:
                summary[dtype] = {"count": 0, "max_severity": 0, "total_area": 0}
            summary[dtype]["count"] += 1
            summary[dtype]["max_severity"] = max(summary[dtype]["max_severity"], damage["severity"])
            summary[dtype]["total_area"] += damage.get("area", 0)
        return summary
