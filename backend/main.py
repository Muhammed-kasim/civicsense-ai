from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
import shutil
from datetime import datetime
from typing import Optional

from database.db import get_db, init_db
from ml_models.damage_detector import DamageDetector
from ml_models.fake_detector import FakeImageDetector
from ml_models.geo_analyzer import GeoAnalyzer
from ml_models.tone_analyzer import ToneAnalyzer
from ml_models.priority_engine import PriorityEngine
from ml_models.image_comparator import ImageComparator
from ml_models.sms_service import SMSService

app = FastAPI(title="CivicSense AI - Infrastructure Complaint System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

damage_detector = DamageDetector()
fake_detector = FakeImageDetector()
geo_analyzer = GeoAnalyzer()
tone_analyzer = ToneAnalyzer()
image_comparator = ImageComparator()

sms_service = SMSService(provider="console")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "CivicSense AI - Infrastructure Complaint System", "status": "running"}

@app.post("/api/complaints")
async def create_complaint(
    complainant_name: str = Form(...),
    phone: str = Form(...),
    complaint_text: str = Form(...),
    city: str = Form(""),
    village: str = Form(""),
    state: str = Form(""),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    db = get_db()
    cursor = db.cursor()
    
    tone_analysis = tone_analyzer.analyze(complaint_text)
    
    cursor.execute("""
        INSERT INTO complaints 
        (complainant_name, phone, complaint_text, category, emergency_level, 
         danger_score, latitude, longitude, city, village, state, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        complainant_name, phone, complaint_text,
        tone_analysis["category"], tone_analysis["emergency_level"],
        tone_analysis["danger_score"], latitude, longitude,
        city, village, state
    ))
    
    complaint_id = cursor.lastrowid
    
    image_analysis = None
    if image:
        image_path = os.path.join(UPLOAD_DIR, f"{complaint_id}_{image.filename}")
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        fake_analysis = fake_detector.analyze(image_path)
        
        damage_analysis = damage_detector.analyze_image(image_path)
        
        geo_data = geo_analyzer.estimate_location_from_context(image_path, complaint_text)
        
        cursor.execute("""
            INSERT INTO images 
            (complaint_id, image_path, image_type, is_fake, is_old, has_damage,
             damage_type, damage_severity, EXIF_latitude, EXIF_longitude, EXIF_date)
            VALUES (?, ?, 'initial', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id, image_path,
            1 if fake_analysis.get("is_fake") else 0,
            1 if fake_analysis.get("is_old") else 0,
            1 if damage_analysis.get("total_damages", 0) > 0 else 0,
            json.dumps(damage_analysis.get("damage_summary", {})),
            damage_analysis.get("overall_severity", 0),
            geo_data.get("estimated_location", {}).get("latitude") if geo_data.get("estimated_location") else latitude,
            geo_data.get("estimated_location", {}).get("longitude") if geo_data.get("estimated_location") else longitude,
            fake_analysis.get("metadata", {}).get("date_taken", "")
        ))
        
        if not latitude and geo_data.get("estimated_location"):
            latitude = geo_data["estimated_location"].get("latitude")
            longitude = geo_data["estimated_location"].get("longitude")
            cursor.execute(
                "UPDATE complaints SET latitude = ?, longitude = ? WHERE id = ?",
                (latitude, longitude, complaint_id)
            )
        
        image_analysis = {
            "fake_analysis": fake_analysis,
            "damage_analysis": damage_analysis,
            "geo_analysis": geo_data
        }
    else:
        geo_data = {"city": city, "village": village, "has_gps": False}
        damage_analysis = None
    
    if image_analysis:
        priority_data = PriorityEngine(db.name).calculate_priority(
            {"category": tone_analysis["category"], "city": city, "village": village},
            tone_analysis,
            damage_analysis["damage_analysis"],
            geo_data
        )
    else:
        priority_data = PriorityEngine(db.name).calculate_priority(
            {"category": tone_analysis["category"], "city": city, "village": village},
            tone_analysis,
            None,
            geo_data
        )
    
    cursor.execute("""
        UPDATE complaints SET 
        emergency_level = ?, danger_score = ?, assigned_to = ?
        WHERE id = ?
    """, (
        tone_analysis["emergency_level"],
        priority_data["final_score"],
        priority_data.get("assigned_official", {}).get("name", ""),
        complaint_id
    ))
    
    db.commit()
    
    sms_targets = priority_data.get("sms_targets", [])
    sms_results = []
    if sms_targets:
        sms_results = sms_service.send_complaint_notification(
            complaint_id,
            {
                "category": tone_analysis["category"],
                "complaint_text": complaint_text,
                "city": city,
                "village": village,
                "has_children_vulnerability": tone_analysis.get("has_children_vulnerability", False)
            },
            priority_data,
            sms_targets
        )
    
    db.close()
    
    return {
        "complaint_id": complaint_id,
        "status": "created",
        "tone_analysis": tone_analysis,
        "priority": priority_data,
        "image_analysis": image_analysis,
        "sms_notifications": sms_results,
        "message": "Complaint registered successfully"
    }

@app.post("/api/complaints/{complaint_id}/images")
async def upload_after_image(
    complaint_id: int,
    image: UploadFile = File(...)
):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    complaint = cursor.fetchone()
    
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    image_path = os.path.join(UPLOAD_DIR, f"{complaint_id}_after_{image.filename}")
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    fake_analysis = fake_detector.analyze(image_path)
    
    damage_analysis = damage_detector.analyze_image(image_path)
    
    cursor.execute("""
        INSERT INTO images 
        (complaint_id, image_path, image_type, is_fake, is_old, has_damage,
         damage_type, damage_severity)
        VALUES (?, ?, 'after', ?, ?, ?, ?, ?)
    """, (
        complaint_id, image_path,
        1 if fake_analysis.get("is_fake") else 0,
        1 if fake_analysis.get("is_old") else 0,
        1 if damage_analysis.get("total_damages", 0) > 0 else 0,
        json.dumps(damage_analysis.get("damage_summary", {})),
        damage_analysis.get("overall_severity", 0)
    ))
    
    after_image_id = cursor.lastrowid
    
    cursor.execute("""
        SELECT id, image_path FROM images 
        WHERE complaint_id = ? AND image_type = 'initial'
        ORDER BY created_at DESC LIMIT 1
    """, (complaint_id,))
    before_image = cursor.fetchone()
    
    verification_result = None
    if before_image:
        verification_result = image_comparator.compare_images(
            before_image["image_path"], image_path
        )
        
        cursor.execute("""
            INSERT INTO verifications 
            (complaint_id, before_image_id, after_image_id, is_verified, 
             verification_notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            complaint_id, before_image["id"], after_image_id,
            1 if verification_result["is_verified"] else 0,
            verification_result["verification_notes"]
        ))
        
        if verification_result["is_verified"]:
            cursor.execute(
                "UPDATE complaints SET status = 'verified_fixed' WHERE id = ?",
                (complaint_id,)
            )
        else:
            cursor.execute(
                "UPDATE complaints SET status = 'needs_review' WHERE id = ?",
                (complaint_id,)
            )
    
    db.commit()
    db.close()
    
    return {
        "after_image_id": after_image_id,
        "fake_analysis": fake_analysis,
        "damage_analysis": damage_analysis,
        "verification": verification_result,
        "status": "After image uploaded and analyzed"
    }

@app.get("/api/complaints")
def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    priority_tier: Optional[str] = None
):
    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT * FROM complaints WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if city:
        query += " AND city = ?"
        params.append(city)
    
    query += " ORDER BY danger_score DESC, created_at DESC"
    
    cursor.execute(query, params)
    complaints = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "complaints": complaints,
        "total": len(complaints)
    }

@app.get("/api/complaints/{complaint_id}")
def get_complaint(complaint_id: int):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    complaint = cursor.fetchone()
    
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    cursor.execute("SELECT * FROM images WHERE complaint_id = ?", (complaint_id,))
    images = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM verifications WHERE complaint_id = ?", (complaint_id,))
    verifications = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM sms_logs WHERE complaint_id = ?", (complaint_id,))
    sms_logs = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "complaint": dict(complaint),
        "images": images,
        "verifications": verifications,
        "sms_logs": sms_logs
    }

@app.put("/api/complaints/{complaint_id}/status")
def update_status(
    complaint_id: int,
    status: str = Form(...),
    notes: str = Form("")
):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("UPDATE complaints SET status = ?, updated_at = ? WHERE id = ?",
                   (status, datetime.now().isoformat(), complaint_id))
    
    db.commit()
    db.close()
    
    return {"status": "updated", "new_status": status}

@app.post("/api/complaints/{complaint_id}/verify")
async def verify_fix(
    complaint_id: int,
    after_image: UploadFile = File(...)
):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    complaint = cursor.fetchone()
    
    if not complaint:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    image_path = os.path.join(UPLOAD_DIR, f"{complaint_id}_verify_{after_image.filename}")
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(after_image.file, buffer)
    
    cursor.execute("""
        SELECT id, image_path FROM images 
        WHERE complaint_id = ? AND image_type = 'initial'
        ORDER BY created_at DESC LIMIT 1
    """, (complaint_id,))
    before_image = cursor.fetchone()
    
    if not before_image:
        db.close()
        raise HTTPException(status_code=400, detail="No initial image found for comparison")
    
    verification_result = image_comparator.compare_images(
        before_image["image_path"], image_path
    )
    
    cursor.execute("""
        INSERT INTO images 
        (complaint_id, image_path, image_type, has_damage, damage_severity)
        VALUES (?, ?, 'verification', ?, ?)
    """, (
        complaint_id, image_path,
        1 if verification_result.get("after_damage_level", 0) > 0.3 else 0,
        verification_result.get("after_damage_level", 0)
    ))
    
    after_image_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO verifications 
        (complaint_id, before_image_id, after_image_id, is_verified, 
         verification_notes, verified_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        complaint_id, before_image["id"], after_image_id,
        1 if verification_result["is_verified"] else 0,
        verification_result["verification_notes"],
        datetime.now().isoformat()
    ))
    
    if verification_result["is_verified"]:
        cursor.execute(
            "UPDATE complaints SET status = 'verified_fixed' WHERE id = ?",
            (complaint_id,)
        )
        status = "verified_fixed"
    else:
        cursor.execute(
            "UPDATE complaints SET status = 'needs_review' WHERE id = ?",
            (complaint_id,)
        )
        status = "needs_review"
    
    db.commit()
    db.close()
    
    return {
        "verification": verification_result,
        "status": status,
        "message": "Fix verified" if verification_result["is_verified"] else "Fix needs review"
    }

@app.get("/api/analytics/danger-zones")
def get_danger_zones():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT city, village, 
               COUNT(*) as complaint_count,
               AVG(danger_score) as avg_danger,
               MAX(danger_score) as max_danger,
               SUM(CASE WHEN emergency_level >= 4 THEN 1 ELSE 0 END) as critical_count
        FROM complaints 
        GROUP BY city, village
        ORDER BY avg_danger DESC
    """)
    
    zones = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return {"danger_zones": zones}

@app.get("/api/analytics/category-stats")
def get_category_stats():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT category,
               COUNT(*) as count,
               AVG(danger_score) as avg_danger,
               SUM(CASE WHEN status = 'verified_fixed' THEN 1 ELSE 0 END) as fixed_count,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count
        FROM complaints 
        GROUP BY category
        ORDER BY avg_danger DESC
    """)
    
    stats = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return {"category_stats": stats}

@app.post("/api/officials")
def add_official(
    name: str = Form(...),
    role: str = Form(...),
    phone: str = Form(...),
    department: str = Form(...),
    city: str = Form(""),
    village: str = Form("")
):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        INSERT INTO officials (name, role, phone, department, city, village)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, role, phone, department, city, village))
    
    official_id = cursor.lastrowid
    db.commit()
    db.close()
    
    return {"official_id": official_id, "message": "Official added"}

@app.post("/api/city-resources")
def update_city_resources(
    city: str = Form(...),
    village: str = Form(""),
    available_workers: int = Form(0),
    available_vehicles: int = Form(0),
    available_materials: str = Form(""),
    emergency_capacity: str = Form("normal")
):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        INSERT INTO city_resources 
        (city, village, available_workers, available_vehicles, 
         available_materials, emergency_capacity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (city, village, available_workers, available_vehicles, 
          available_materials, emergency_capacity))
    
    db.commit()
    db.close()
    
    return {"message": "City resources updated"}

@app.get("/api/dashboard")
def get_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM complaints")
    total = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as pending FROM complaints WHERE status = 'pending'")
    pending = cursor.fetchone()["pending"]
    
    cursor.execute("SELECT COUNT(*) as fixed FROM complaints WHERE status = 'verified_fixed'")
    fixed = cursor.fetchone()["fixed"]
    
    cursor.execute("SELECT COUNT(*) as critical FROM complaints WHERE emergency_level >= 4")
    critical = cursor.fetchone()["critical"]
    
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM complaints GROUP BY category ORDER BY count DESC LIMIT 5
    """)
    top_categories = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT city, COUNT(*) as count, AVG(danger_score) as avg_danger
        FROM complaints GROUP BY city ORDER BY avg_danger DESC LIMIT 5
    """)
    top_cities = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE status = 'pending' 
        ORDER BY danger_score DESC 
        LIMIT 10
    """)
    urgent_complaints = [dict(row) for row in cursor.fetchall()]
    
    db.close()
    
    return {
        "total_complaints": total,
        "pending": pending,
        "fixed": fixed,
        "critical": critical,
        "top_categories": top_categories,
        "top_cities": top_cities,
        "urgent_complaints": urgent_complaints
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
