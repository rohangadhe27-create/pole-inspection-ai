import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration with environment variable fallbacks."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "power-line-pole-ai-secret-key-2026")
    
    # Database Configuration
    # Supported DB_TYPE values: 'mysql' or 'sqlite'
    DB_TYPE = os.getenv("DB_TYPE", "mysql")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "power_line_inspection")
    
    # SQLite fallback database file path
    SQLITE_DB_PATH = str(BASE_DIR / "database" / "power_line_inspection.db")
    
    # Upload Directories
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads" / "inspections")
    ANNOTATED_FOLDER = str(BASE_DIR / "static" / "uploads" / "annotated")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max image size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Model Configuration
    MODEL_PATH = str(BASE_DIR / "model" / "best.pt")
    
    # Defect Classes Supported by AI Module
    DEFECT_CLASSES = [
        "Good Insulator",
        "Broken Insulator",
        "Flashover/Damaged Insulator"
    ]
    
    # Configurable Severity Mapping
    # Easily extendable for new defects (e.g., "Corrosion", "Loose Hardware", "Vegetation")
    DEFECT_SEVERITY_MAP = {
        "Good Insulator": "LOW",
        "Broken Insulator": "HIGH",
        "Flashover/Damaged Insulator": "HIGH",
        "Flashover Insulator": "HIGH",
        "Damaged Insulator": "HIGH",
        "Corrosion / Rust": "MEDIUM",
        "Loose Hardware": "MEDIUM",
        "Vegetation Encroachment": "MEDIUM",
        "Normal": "LOW"
    }
    
    # Configurable Maintenance Recommendations
    MAINTENANCE_RECOMMENDATIONS = {
        "HIGH": "Immediate inspection and replacement recommended.",
        "MEDIUM": "Schedule maintenance inspection.",
        "LOW": "Continue regular monitoring.",
        "NORMAL": "Continue regular monitoring."
    }
    
    # Maintenance Workflow Stages
    MAINTENANCE_STAGES = [
        "Pending",
        "Assigned",
        "In Progress",
        "Repaired",
        "Verified"
    ]
