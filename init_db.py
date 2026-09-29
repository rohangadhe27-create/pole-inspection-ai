"""
Database initialization and seeding script.
Run this script to set up database tables and populate sample demo records:
    python init_db.py
"""

from database.db import init_database, get_db_backend
from scripts.generate_samples import create_sample_images

def main():
    print("====================================================================")
    print("GridSense AI - Initializing Database & Demonstration Assets")
    print("====================================================================")
    
    # 1. Generate sample inspection images
    print("[1/2] Generating realistic sample insulator inspection images...")
    create_sample_images()
    
    # 2. Initialize database schema & seed sample records
    print("[2/2] Initializing database tables and seeding sample records...")
    init_database(force_reseed=True)
    
    backend = get_db_backend()
    print(f"\nSUCCESS: Database successfully initialized using backend: [{backend.upper()}]")
    if backend == "sqlite":
        print("Note: SQLite was used because no active MySQL server was detected.")
        print("To switch to MySQL, update DB_TYPE=mysql and credentials in .env, then re-run python init_db.py")
    print("====================================================================")

if __name__ == "__main__":
    main()
