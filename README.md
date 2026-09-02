# CivicSense AI - Infrastructure Complaint System

AI-powered complaint management for infrastructure issues (potholes, floods, building damage, etc.) that:
- Detects damage in uploaded images (scratches, potholes, cracks, floods)
- Blocks fake/old internet photos
- Estimates location from images (GPS/EXIF + visual/text context)
- Analyzes complaint tone to categorize emergency level & vulnerability
- Prioritizes the most dangerous zones first
- Routes complaints to the exact responsible official (water -> water dept, etc.)
- Verifies fixes by comparing before/after photos
- Sends SMS to officials with resource/prioritization info

## Tech Stack
- **Frontend:** Next.js 14 + TailwindCSS + TypeScript
- **Backend:** Python FastAPI
- **ML:** OpenCV (image analysis), custom heuristic models
- **Database:** SQLite

## Folder Structure
```
backend/          Python FastAPI + ML models
frontend/         Next.js web app
```

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python database/db.py        # create tables
python seed_data.py          # add sample officials & city resources
python main.py               # start API on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                  # start site on http://localhost:3000
```

Open **http://localhost:3000** in your browser.

## Features
- Dashboard with stats, top categories, most affected areas, urgent complaints
- File complaint with AI photo analysis
- All complaints ranked by danger score
- Danger-zone ranking (critical areas first)
- Verify fixes with before/after image comparison
