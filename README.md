# AI-Based Power Line Pole Inspection and Maintenance Recommendation System

An intelligent, college-level web prototype that automates the visual inspection of electrical power line poles and ceramic insulators using Deep Learning (YOLOv8 & OpenCV), determines defect severity, prescribes operational maintenance recommendations, and tracks asset maintenance lifecycles in a relational database.

---

## 📌 Project Overview

Traditional utility pole and insulator inspections require hazardous manual climbing or visual sweeps. This system provides a web-based automated inspection dashboard:
1. **Pole Asset Identification:** Identifies poles by unique ID (e.g. `P-104`) or QR-code tagging.
2. **AI Defect Detection:** Employs YOLOv8 computer vision to inspect insulator imagery and localize defects with bounding boxes.
3. **Multi-Class Classification:**
   - `Good Insulator` (Intact ceramic discs)
   - `Broken Insulator` (Fractured, missing discs)
   - `Flashover/Damaged Insulator` (Electrical arc scorch, carbon burn tracks)
4. **Automated Severity Assessment:** Maps detected defects to severity tiers (`HIGH`, `MEDIUM`, `LOW / NORMAL`).
5. **Operational Recommendations:** Generates actionable maintenance instructions based on severity.
6. **Maintenance Lifecycle Workflow:** Tracks repair progression through 5 stages:
   $$\text{Pending} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Repaired} \longrightarrow \text{Verified}$$
7. **Interactive Dashboard & Asset History:** Displays fleet-wide statistics, defect distributions with Chart.js, and inspection histories per pole.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+ / Python 3.14, Flask, Werkzeug
- **AI & Computer Vision:** Ultralytics YOLOv8, OpenCV, NumPy, Pillow
- **Database:** MySQL (via PyMySQL) with seamless zero-config SQLite automatic fallback
- **Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5.3, FontAwesome 6, Chart.js

---

## 📂 Project Structure

```text
pole_inspection_ai/
├── app.py                      # Flask Application Entry Point & Dashboard
├── config.py                   # Central Application & Severity Configuration
├── requirements.txt            # Python Dependencies
├── .env                        # Environment Variables (Secrets & DB Config)
├── .env.example                # Template Environment Variables
├── init_db.py                  # Standalone Database Seeder & Setup Script
├── test_app.py                 # Full Automated Unit & Integration Test Suite
├── model/
│   ├── README.md               # Guide on dropping in custom trained YOLO weights
│   └── best.pt                 # Custom trained YOLOv8 weights (drop-in)
├── ai/
│   ├── __init__.py
│   └── detector.py             # YOLO Inference Engine, Demo Fallback & OpenCV Annotator
├── database/
│   ├── db.py                   # Unified MySQL / SQLite Abstraction Layer
│   ├── schema.sql              # MySQL DDL Schema & Sample Seed Data
│   └── power_line_inspection.db# Local SQLite Database (auto-generated fallback)
├── routes/
│   ├── __init__.py
│   ├── inspection.py           # Upload, AI Analysis & Save Handlers
│   ├── poles.py                # Pole Asset Registry & Pole History
│   └── maintenance.py          # Maintenance Workflow Board & Reports
├── static/
│   ├── css/
│   │   └── style.css           # Custom Engineering Dashboard Theme
│   ├── js/
│   │   └── main.js             # Client-side Interactions & Utilities
│   ├── sample_images/          # High-resolution Demonstration Insulator Images
│   └── uploads/
│       ├── inspections/        # Raw Uploaded Inspection Photos
│       └── annotated/          # OpenCV Bounding Box Annotated Visuals
└── templates/
    ├── base.html               # Responsive Shell with Sidebar & Status Badges
    ├── dashboard.html          # Operational Dashboard with Chart.js Graphs
    ├── inspection.html         # New Inspection Upload & AI Detection Interface
    ├── poles.html              # Transmission & Distribution Pole Directory
    ├── history.html            # Asset History, Timeline & Recommendations
    ├── inspections.html        # Comprehensive Filterable Inspections Log
    ├── defects.html            # High-Priority Critical Defect Triage Board
    ├── maintenance.html        # 5-Stage Maintenance Lifecycle Manager
    ├── reports.html            # Executive Audit Summary & Print View
    ├── 404.html                # 404 Error Page
    └── 500.html                # 500 Server Error Page
```

---

## 🚀 Quick Setup & Installation

### Step 1: Clone or Navigate to Project Directory
```powershell
cd "f:\pole with ai"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Database Configuration (MySQL or SQLite)
The system supports both **MySQL** and **SQLite**.

#### Option A: Zero-Config SQLite (Default Fallback)
If you do not have MySQL installed, no configuration is needed. The system automatically detects this and initializes an SQLite database with identical tables and seed data.

#### Option B: MySQL Setup (Production Mode)
1. Open your MySQL client (e.g. phpMyAdmin, MySQL Workbench, or CLI).
2. Import `database/schema.sql` or let `init_db.py` create it.
3. Configure your `.env` file:
   ```ini
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=power_line_inspection
   ```

### Step 4: Initialize Sample Data
Run the initialization script to generate demonstration images and seed poles, inspections, and maintenance tasks:
```powershell
python init_db.py
```

### Step 5: Run Automated Tests
Verify all endpoints and AI detectors:
```powershell
python test_app.py
```
*(All 8 tests should pass with `OK` status)*

### Step 6: Launch the Web Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🎯 Step-by-Step College Demonstration Flow

Follow this exact sequence during your project evaluation or presentation:

| Step | Action | What to Point Out to Evaluator |
|---|---|---|
| **1. Dashboard** | Open `http://127.0.0.1:5000` | Show summary KPI cards (*Total Poles: 6, Inspected: 5, Defects: 3, Critical: 2*), Chart.js defect doughnut chart, and pole network status chart. |
| **2. Select New Inspection** | Click **New Inspection** on sidebar or topbar | Point out the clean UI, pole identification field, and QR code scan simulation modal. |
| **3. Pole Selection** | Enter `P-104` or click quick pre-fill tag | Shows manual Pole ID assignment for asset tracking. |
| **4. Load Inspection Image** | Click **"Broken Insulator (P-104)"** button under Quick Test Samples | An insulator inspection photo is loaded into the dropzone. |
| **5. Run AI Detection** | Click **"Analyze Image with AI"** | YOLO / OpenCV processes the image in real-time. |
| **6. Defect & Confidence** | Observe the results panel | Points out **Detected Defect: Broken Insulator**, **Confidence: 94.2%**, and the OpenCV bounding box drawn around the damaged ceramic discs. |
| **7. Severity Calculation** | Look at the severity badge | Shows **Severity: HIGH** (Red indicator). Explain that severity logic is configurable in `config.py`. |
| **8. Maintenance Recommendation** | Review the recommendation card | Displays operational advice: *"Immediate inspection and replacement recommended."* |
| **9. Save Inspection** | Click **"Save Inspection Record"** | Saves the record in the database, automatically updates Pole `P-104` status to **Critical**, and automatically creates a linked maintenance order. |
| **10. View Pole History** | The system navigates to `http://127.0.0.1:5000/poles/P-104` | Displays GPS coordinates (Lat `13.0875`, Lng `80.2750`), installation date, latest recommendation banner, full inspection timeline, and previous maintenance tasks. |
| **11. Maintenance Workflow** | Navigate to **Maintenance** (`/maintenance`) | Shows the 5-stage pipeline: `Pending → Assigned → In Progress → Repaired → Verified`. |
| **12. Update Status** | Click **"Update Status"** on Task #1 | Change status to `In Progress` or `Repaired`, assign technician `"John Doe"`, and save. Note how the pole's health status restores once repairs are verified! |

---

## 🧠 AI Module & Custom YOLO Integration

### Replacing the Model with Your Own Trained YOLO Weights
1. Train a YOLOv8 model (e.g. `yolov8n` or `yolov8s`) on your power line insulator dataset using the Ultralytics CLI:
   ```bash
   yolo detect train model=yolov8n.pt data=insulators.yaml epochs=50 imgsz=640
   ```
2. Copy your resulting `best.pt` file into the `model/` directory:
   ```
   model/
   └── best.pt
   ```
3. Restart the Flask app (`python app.py`).
4. The system automatically detects `model/best.pt`, loads it into memory via `ultralytics.YOLO("model/best.pt")`, and switches the topbar badge from **"Demo AI Mode"** to **"YOLOv8 Active"**!

### Transparent Demo Mode
If custom weights are not present, the system runs in **Demo Mode**, generating realistic bounding boxes and OpenCV overlays. It is **transparently labeled** in the API responses, template badges, and image watermarks so no evaluator is misled.

---

## ⚙️ Configurable Severity & Recommendation Logic

Rules are decoupled from database queries in `config.py` so additional defects can be added without altering the database schema:

```python
# Easily extendable for new defects
DEFECT_SEVERITY_MAP = {
    "Good Insulator": "LOW",
    "Broken Insulator": "HIGH",
    "Flashover/Damaged Insulator": "HIGH",
    "Corrosion / Rust": "MEDIUM",
    "Loose Hardware": "MEDIUM",
    "Vegetation Encroachment": "MEDIUM",
    "Normal": "LOW"
}

MAINTENANCE_RECOMMENDATIONS = {
    "HIGH": "Immediate inspection and replacement recommended.",
    "MEDIUM": "Schedule maintenance inspection.",
    "LOW": "Continue regular monitoring.",
    "NORMAL": "Continue regular monitoring."
}
```

---

## 🗄️ Database Schema Reference

### 1. `poles` Table
| Column | Type | Description |
|---|---|---|
| `pole_id` | VARCHAR(50) PK | Unique Pole Identifier (e.g. `P-001`, `P-104`) |
| `latitude` | DECIMAL(10, 7) | GPS Latitude coordinate |
| `longitude` | DECIMAL(10, 7) | GPS Longitude coordinate |
| `installation_date` | DATE | Commissioning date |
| `status` | VARCHAR(50) | Asset status (`Normal`, `Warning`, `Critical`) |

### 2. `inspections` Table
| Column | Type | Description |
|---|---|---|
| `inspection_id` | INT PK AUTO_INCREMENT | Unique inspection record ID |
| `pole_id` | VARCHAR(50) FK | Associated pole asset |
| `inspection_date` | DATETIME | Timestamp of inspection |
| `image_path` | VARCHAR(255) | Path to original / annotated photo |
| `defect_type` | VARCHAR(100) | Classified defect (`Good Insulator`, `Broken Insulator`, etc.) |
| `confidence` | DECIMAL(5, 2) | Detection confidence score (0 - 100%) |
| `severity` | VARCHAR(20) | Assessed severity (`HIGH`, `MEDIUM`, `LOW`) |
| `recommendation`| TEXT | Generated operational maintenance advice |
| `status` | VARCHAR(50) | State (`Completed`, `Action Required`) |

### 3. `maintenance` Table
| Column | Type | Description |
|---|---|---|
| `maintenance_id` | INT PK AUTO_INCREMENT | Unique maintenance task ID |
| `inspection_id` | INT FK (NULLABLE) | Source inspection trigger |
| `pole_id` | VARCHAR(50) FK | Pole under maintenance |
| `action` | VARCHAR(255) | Required repair / replacement procedure |
| `assigned_to` | VARCHAR(100) | Technician / crew assigned |
| `maintenance_date`| DATETIME | Scheduled or completion timestamp |
| `status` | VARCHAR(50) | Lifecycle stage (`Pending`, `Assigned`, `In Progress`, `Repaired`, `Verified`) |
| `remarks` | TEXT | Work order remarks and safety notes |

---

## 🛡️ Security & Best Practices

1. **Environment Variables:** Secrets, database credentials, and paths are isolated in `.env` and never hardcoded in client-side code.
2. **File Upload Security:** Files are validated using `werkzeug.utils.secure_filename` and restricted to approved extensions (`.jpg`, `.jpeg`, `.png`, `.webp`) with a 16MB file size limit.
3. **Structured Storage:** Images are partitioned into `static/uploads/inspections` and `static/uploads/annotated`.
4. **Resilient Database Layer:** Automatic fallback ensures the app never crashes during demonstration if a local MySQL daemon is offline.
5. **No IoT / Drone Bloat:** Built strictly according to project specifications as a practical software and computer vision prototype.

---

## 🎓 Academic Presentation Notes

- **Objective Met:** Implements a closed-loop engineering workflow from image acquisition to AI classification, bounding-box localization, severity scoring, and maintenance order generation.
- **Terminology Accuracy:** Labeled honestly as a **Maintenance Recommendation System** based on observable computer vision defects, rather than making unverified claims of "predictive maintenance".
- **Extensible Architecture:** Adding new defect classes (e.g., cross-arm rot, bird caging, loose dampeners) requires only adding a class name to `config.py` and retraining YOLO weights.
