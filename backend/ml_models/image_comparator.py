import cv2
import numpy as np
from typing import Dict, List, Tuple
import os

class ImageComparator:
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def compare_images(self, before_path: str, after_path: str) -> Dict:
        before_img = cv2.imread(before_path)
        after_img = cv2.imread(after_path)
        
        if before_img is None or after_img is None:
            return {"error": "Could not load one or both images"}
        
        before_resized = cv2.resize(before_img, (640, 480))
        after_resized = cv2.resize(after_img, (640, 480))
        
        structural_similarity = self._structural_similarity(before_resized, after_resized)
        
        color_diff = self._color_difference(before_resized, after_resized)
        
        edge_change = self._edge_change(before_resized, after_resized)
        
        damage_change = self._damage_change(before_resized, after_resized)
        
        before_damage = self._assess_damage(before_resized)
        after_damage = self._assess_damage(after_resized)
        
        improvement = self._calculate_improvement(before_damage, after_damage)
        
        is_verified = self._determine_verification(
            structural_similarity, color_diff, edge_change, improvement
        )
        
        return {
            "structural_similarity": round(structural_similarity, 3),
            "color_difference": round(color_diff, 3),
            "edge_change": round(edge_change, 3),
            "damage_change": round(damage_change, 3),
            "before_damage_level": round(before_damage, 3),
            "after_damage_level": round(after_damage, 3),
            "improvement": round(improvement, 3),
            "is_verified": is_verified,
            "verification_notes": self._generate_notes(
                structural_similarity, color_diff, edge_change, improvement, is_verified
            )
        }
    
    def _structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.GaussianBlur(gray1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(gray2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu1_mu2
        
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        
        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / \
                   ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        
        return float(np.mean(ssim_map))
    
    def _color_difference(self, img1: np.ndarray, img2: np.ndarray) -> float:
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
        
        diff = cv2.absdiff(hsv1, hsv2)
        
        mean_diff = np.mean(diff) / 255.0
        
        return mean_diff
    
    def _edge_change(self, img1: np.ndarray, img2: np.ndarray) -> float:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        edges1 = cv2.Canny(gray1, 50, 150)
        edges2 = cv2.Canny(gray2, 50, 150)
        
        diff = cv2.absdiff(edges1, edges2)
        
        change_ratio = np.sum(diff > 0) / diff.size
        
        return change_ratio
    
    def _damage_change(self, img1: np.ndarray, img2: np.ndarray) -> float:
        damage1 = self._detect_damage_regions(img1)
        damage2 = self._detect_damage_regions(img2)
        
        if len(damage1) == 0 and len(damage2) == 0:
            return 0.0
        
        change = len(damage2) - len(damage1)
        max_damage = max(len(damage1), len(damage2), 1)
        
        return change / max_damage
    
    def _detect_damage_regions(self, img: np.ndarray) -> List:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        damage_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:
                x, y, w, h = cv2.boundingRect(contour)
                damage_regions.append({"x": x, "y": y, "w": w, "h": h, "area": area})
        
        return damage_regions
    
    def _assess_damage(self, img: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = np.sum(thresh > 0) / thresh.size
        
        damage_score = (edge_density * 0.6 + dark_ratio * 0.4)
        
        return min(1.0, damage_score * 3)
    
    def _calculate_improvement(self, before_damage: float, after_damage: float) -> float:
        if before_damage == 0:
            return 0.0
        
        improvement = (before_damage - after_damage) / before_damage
        
        return max(-1.0, min(1.0, improvement))
    
    def _determine_verification(self, similarity: float, color_diff: float, 
                               edge_change: float, improvement: float) -> bool:
        checks_passed = 0
        total_checks = 0
        
        if similarity > 0.5:
            checks_passed += 1
        total_checks += 1
        
        if color_diff > 0.05:
            checks_passed += 1
        total_checks += 1
        
        if edge_change > 0.02:
            checks_passed += 1
        total_checks += 1
        
        if improvement > 0.1:
            checks_passed += 1
        total_checks += 1
        
        return checks_passed >= total_checks * 0.5
    
    def _generate_notes(self, similarity: float, color_diff: float, 
                       edge_change: float, improvement: float, is_verified: bool) -> str:
        notes = []
        
        if is_verified:
            notes.append("Fix appears to be verified - changes detected between before/after images")
        else:
            notes.append("Fix could not be verified - images may be too similar or different angles")
        
        if improvement > 0.3:
            notes.append(f"Significant improvement detected ({improvement:.0%})")
        elif improvement > 0.1:
            notes.append(f"Moderate improvement detected ({improvement:.0%})")
        elif improvement < -0.1:
            notes.append(f"Situation appears worse after fix ({improvement:.0%})")
        
        if similarity > 0.8:
            notes.append("Images appear to be from same location")
        elif similarity < 0.3:
            notes.append("Warning: Images may be from different locations")
        
        return "; ".join(notes)
