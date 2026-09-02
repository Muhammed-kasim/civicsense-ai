import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "complaints.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complainant_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            complaint_text TEXT NOT NULL,
            category TEXT NOT NULL,
            emergency_level INTEGER DEFAULT 0,
            danger_score REAL DEFAULT 0,
            latitude REAL,
            longitude REAL,
            city TEXT,
            village TEXT,
            state TEXT,
            status TEXT DEFAULT 'pending',
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            image_type TEXT DEFAULT 'initial',
            is_fake INTEGER DEFAULT 0,
            is_old INTEGER DEFAULT 0,
            has_damage INTEGER DEFAULT 0,
            damage_type TEXT,
            damage_severity REAL DEFAULT 0,
            EXIF_latitude REAL,
            EXIF_longitude REAL,
            EXIF_date TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS damage_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id INTEGER NOT NULL,
            damage_type TEXT NOT NULL,
            damage_description TEXT,
            severity REAL DEFAULT 0,
            location_in_image TEXT,
            bbox_x INTEGER,
            bbox_y INTEGER,
            bbox_w INTEGER,
            bbox_h INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (image_id) REFERENCES images(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sms_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            recipient_phone TEXT NOT NULL,
            recipient_name TEXT,
            recipient_role TEXT,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'sent',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS officials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT,
            village TEXT,
            state TEXT,
            department TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            village TEXT,
            available_workers INTEGER DEFAULT 0,
            available_vehicles INTEGER DEFAULT 0,
            available_materials TEXT,
            emergency_capacity TEXT DEFAULT 'normal',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            before_image_id INTEGER,
            after_image_id INTEGER,
            is_verified INTEGER DEFAULT 0,
            verification_notes TEXT,
            verified_by TEXT,
            verified_at TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id),
            FOREIGN KEY (before_image_id) REFERENCES images(id),
            FOREIGN KEY (after_image_id) REFERENCES images(id)
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
