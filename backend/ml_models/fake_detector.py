import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
import json
from datetime import datetime
from typing import Dict, Optional

class FakeImageDetector:
    def __init__(self):
        self.min_image_size = 100
        self.max_age_days = 90
    
    def analyze(self, image_path: str) -> Dict:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not load image", "is_fake": True, "confidence": 0.9}
        
        results = {
            "is_fake": False,
            "is_old": False,
            "confidence": 0.0,
            "checks": [],
            "metadata": {}
        }
        
        metadata_result = self._extract_metadata(image_path)
        results["metadata"] = metadata_result
        
        if metadata_result.get("has_exif"):
            age_check = self._check_image_age(metadata_result)
            results["checks"].append(age_check)
            if age_check["is_old"]:
                results["is_old"] = True
        
        size_check = self._check_image_quality(img)
        results["checks"].append(size_check)
        
        noise_check = self._check_noise_patterns(img)
        results["checks"].append(noise_check)
        
        compression_check = self._check_compression_artifacts(img)
        results["checks"].append(compression_check)
        
        color_check = self._check_color_consistency(img)
        results["checks"].append(color_check)
        
        edge_check = self._check_edge_consistency(img)
        results["checks"].append(edge_check)
        
        freq_check = self._check_frequency_analysis(img)
        results["checks"].append(freq_check)
        
        results["confidence"] = self._calculate_fake_confidence(results["checks"])
        results["is_fake"] = results["confidence"] > 0.6
        
        return results
    
    def _extract_metadata(self, image_path: str) -> Dict:
        metadata = {
            "has_exif": False,
            "camera_make": None,
            "camera_model": None,
            "date_taken": None,
            "gps_data": None,
            "software": None,
            "raw_metadata": {}
        }
        
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            
            if exif_data:
                metadata["has_exif"] = True
                
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "Make":
                        metadata["camera_make"] = str(value)
                    elif tag == "Model":
                        metadata["camera_model"] = str(value)
                    elif tag == "DateTimeOriginal":
                        metadata["date_taken"] = str(value)
                    elif tag == "Software":
                        metadata["software"] = str(value)
                    elif tag == "GPSInfo":
                        gps_data = {}
                        for gps_tag_id in value:
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = value[gps_tag_id]
                        metadata["gps_data"] = gps_data
                    
                    metadata["raw_metadata"][str(tag)] = str(value)
        
        except Exception as e:
            metadata["error"] = str(e)
        
        return metadata
    
    def _check_image_age(self, metadata: Dict) -> Dict:
        result = {"check": "image_age", "is_old": False, "details": ""}
        
        if metadata.get("date_taken"):
            try:
                date_str = metadata["date_taken"]
                for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                    try:
                        date_taken = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    result["details"] = "Could not parse date"
                    return result
                
                age_days = (datetime.now() - date_taken).days
                result["age_days"] = age_days
                result["date_taken"] = date_str
                
                if age_days > self.max_age_days:
                    result["is_old"] = True
                    result["details"] = f"Image is {age_days} days old (threshold: {self.max_age_days})"
                else:
                    result["details"] = f"Image is {age_days} days old (within threshold)"
            
            except Exception as e:
                result["details"] = f"Error checking age: {str(e)}"
        else:
            result["details"] = "No EXIF date found"
        
        return result
    
    def _check_image_quality(self, img: np.ndarray) -> Dict:
        result = {"check": "image_quality", "score": 0, "details": ""}
        
        h, w = img.shape[:2]
        if h < self.min_image_size or w < self.min_image_size:
            result["score"] = 0.8
            result["details"] = "Image too small - likely low quality or cropped"
            return result
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < 50:
            result["score"] = 0.6
            result["details"] = "Very blurry image"
        elif laplacian_var < 100:
            result["score"] = 0.3
            result["details"] = "Somewhat blurry"
        else:
            result["score"] = 0.0
            result["details"] = "Good sharpness"
        
        result["laplacian_var"] = float(laplacian_var)
        return result
    
    def _check_noise_patterns(self, img: np.ndarray) -> Dict:
        result = {"check": "noise_patterns", "score": 0, "details": ""}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        kernel = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]])
        high_freq = cv2.filter2D(gray, cv2.CV_64F, kernel)
        
        noise_level = np.std(high_freq)
        
        if noise_level < 5:
            result["score"] = 0.5
            result["details"] = "Unnaturally smooth - likely AI-generated or heavily filtered"
        elif noise_level > 50:
            result["score"] = 0.3
            result["details"] = "Unusually noisy"
        else:
            result["score"] = 0.0
            result["details"] = "Normal noise pattern"
        
        result["noise_level"] = float(noise_level)
        return result
    
    def _check_compression_artifacts(self, img: np.ndarray) -> Dict:
        result = {"check": "compression_artifacts", "score": 0, "details": ""}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dct = cv2.dct(np.float32(gray))
        
        block_size = 8
        h, w = gray.shape
        artifact_score = 0
        block_count = 0
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = dct[i:i+block_size, j:j+block_size]
                zigzag = np.concatenate([
                    np.diag(block, k=-i) for i in range(block_size)
                ])
                zero_runs = np.sum(zigzag == 0)
                if zero_runs > 20:
                    artifact_score += 1
                block_count += 1
        
        if block_count > 0:
            artifact_ratio = artifact_score / block_count
            if artifact_ratio > 0.7:
                result["score"] = 0.4
                result["details"] = "Heavy JPEG compression artifacts"
            elif artifact_ratio > 0.4:
                result["score"] = 0.2
                result["details"] = "Moderate compression artifacts"
            else:
                result["score"] = 0.0
                result["details"] = "Minimal compression artifacts"
            
            result["artifact_ratio"] = float(artifact_ratio)
        
        return result
    
    def _check_color_consistency(self, img: np.ndarray) -> Dict:
        result = {"check": "color_consistency", "score": 0, "details": ""}
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        h_hist = h_hist / h_hist.sum()
        
        entropy = -np.sum(h_hist[h_hist > 0] * np.log2(h_hist[h_hist > 0]))
        
        if entropy < 2.0:
            result["score"] = 0.4
            result["details"] = "Unnaturally uniform color distribution"
        elif entropy > 6.5:
            result["score"] = 0.2
            result["details"] = "Extremely varied colors"
        else:
            result["score"] = 0.0
            result["details"] = "Normal color distribution"
        
        result["color_entropy"] = float(entropy)
        return result
    
    def _check_edge_consistency(self, img: np.ndarray) -> Dict:
        result = {"check": "edge_consistency", "score": 0, "details": ""}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        edge_density = np.sum(edges > 0) / edges.size
        
        h, w = edges.shape
        quadrants = [
            edges[:h//2, :w//2],
            edges[:h//2, w//2:],
            edges[h//2:, :w//2],
            edges[h//2:, w//2:]
        ]
        
        densities = [np.sum(q > 0) / q.size for q in quadrants]
        density_std = np.std(densities)
        
        if density_std > 0.1:
            result["score"] = 0.3
            result["details"] = "Inconsistent edge patterns across image"
        else:
            result["score"] = 0.0
            result["details"] = "Consistent edge patterns"
        
        result["edge_density"] = float(edge_density)
        result["density_std"] = float(density_std)
        return result
    
    def _check_frequency_analysis(self, img: np.ndarray) -> Dict:
        result = {"check": "frequency_analysis", "score": 0, "details": ""}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.log(np.abs(f_shift) + 1)
        
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2
        
        low_freq = magnitude[center_h-10:center_h+10, center_w-10:center_w+10]
        high_freq = np.concatenate([
            magnitude[:10, :10],
            magnitude[:10, -10:],
            magnitude[-10:, :10],
            magnitude[-10:, -10:]
        ])
        
        low_mean = np.mean(low_freq)
        high_mean = np.mean(high_freq)
        
        ratio = low_mean / (high_mean + 1)
        
        if ratio > 20:
            result["score"] = 0.3
            result["details"] = "Unusual frequency distribution"
        else:
            result["score"] = 0.0
            result["details"] = "Normal frequency distribution"
        
        result["frequency_ratio"] = float(ratio)
        return result
    
    def _calculate_fake_confidence(self, checks: List[Dict]) -> float:
        if not checks:
            return 0.0
        
        total_score = 0
        for check in checks:
            total_score += check.get("score", 0)
        
        return min(1.0, total_score / len(checks))
