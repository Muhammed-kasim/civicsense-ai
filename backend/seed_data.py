import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "complaints.db")

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    officials = [
        ("Rajesh Kumar", "sdm", "9876543210", "public_works", "Bhopal", "Habibganj", ""),
        ("Priya Singh", "water_engineer", "9876543211", "water_supply", "Bhopal", "Habibganj", ""),
        ("Amit Verma", "electrician", "9876543212", "electricity", "Bhopal", "Kolar", ""),
        ("Sunita Devi", "sanitation_officer", "9876543213", "sanitation", "Bhopal", "Kolar", ""),
        ("Vikram Patel", "municipal_engineer", "9876543214", "municipal", "Bhopal", "", ""),
        ("Ramesh Gupta", "sdm", "9876543215", "public_works", "Indore", "Vijay Nagar", ""),
        ("Meera Joshi", "water_engineer", "9876543216", "water_supply", "Indore", "Palasia", ""),
        ("Suresh Nair", "electrician", "9876543217", "electricity", "Indore", "Rajendra Nagar", ""),
        ("Anita Sharma", "collector", "9876543218", "general", "Bhopal", "", ""),
        ("Deepak Mishra", "collector", "9876543219", "general", "Indore", "", ""),
        ("Kavita Reddy", "fire_chief", "9876543220", "fire_services", "Bhopal", "", ""),
        ("Manoj Tiwari", "forest_officer", "9876543221", "forest", "Bhopal", "", ""),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO officials (name, role, phone, department, city, village, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, officials)
    
    resources = [
        ("Bhopal", "Habibganj", 25, 5, "cement, gravel, pipes", "normal"),
        ("Bhopal", "Kolar", 15, 3, "cement, gravel", "strained"),
        ("Bhopal", "MP Nagar", 30, 8, "full stock", "available"),
        ("Indore", "Vijay Nagar", 20, 4, "cement, gravel, pipes", "normal"),
        ("Indore", "Palasia", 10, 2, "limited stock", "strained"),
        ("Indore", "Rajendra Nagar", 18, 3, "cement, gravel", "normal"),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO city_resources 
        (city, village, available_workers, available_vehicles, available_materials, emergency_capacity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, resources)
    
    conn.commit()
    conn.close()
    print("Seed data inserted successfully!")

if __name__ == "__main__":
    seed()
