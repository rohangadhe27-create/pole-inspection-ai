import os
import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)

# State cache for active database backend
_ACTIVE_BACKEND = None
_MYSQL_TESTED = False
_MYSQL_AVAILABLE = False

def get_db_backend():
    """Returns the current active database backend name ('mysql' or 'sqlite')."""
    global _ACTIVE_BACKEND
    if _ACTIVE_BACKEND is None:
        # Determine backend
        conn = get_connection()
        conn.close()
    return _ACTIVE_BACKEND

def get_connection():
    """
    Attempts to establish a connection based on Config.DB_TYPE.
    If MySQL is configured but fails to connect, automatically falls back to SQLite
    and caches this decision to avoid repeated socket timeouts.
    """
    global _ACTIVE_BACKEND, _MYSQL_TESTED, _MYSQL_AVAILABLE
    
    if Config.DB_TYPE.lower() == "mysql":
        if not _MYSQL_TESTED:
            _MYSQL_TESTED = True
            try:
                import pymysql
                import pymysql.cursors
                
                # Test connection to MySQL server
                conn = pymysql.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False,
                    connect_timeout=1
                )
                
                with conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}`;")
                    cur.execute(f"USE `{Config.DB_NAME}`;")
                conn.commit()
                
                _ACTIVE_BACKEND = "mysql"
                _MYSQL_AVAILABLE = True
                logger.info(f"[DATABASE] Connected to MySQL ({Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME})")
                return conn
            except Exception as e:
                logger.warning(
                    f"[DATABASE] MySQL server not reachable ({e}). "
                    "Using local SQLite fallback database for zero-config demonstration."
                )
                _ACTIVE_BACKEND = "sqlite"
                _MYSQL_AVAILABLE = False
        
        elif _MYSQL_AVAILABLE:
            import pymysql
            import pymysql.cursors
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            return conn
    
    # SQLite backend
    _ACTIVE_BACKEND = "sqlite"
    os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(sql, params=(), fetch=None, fetchone=False, commit=False):
    """
    Unified query execution that works identically on MySQL and SQLite.
    Automatically converts '%s' to '?' when using SQLite.
    When commit=True and fetch is not explicitly True, returns dict with lastrowid and rowcount.
    """
    conn = get_connection()
    backend = _ACTIVE_BACKEND
    
    # Determine default fetch behavior
    if fetch is None:
        fetch = not commit
        
    try:
        if backend == "sqlite":
            sqlite_sql = sql.replace("%s", "?")
            cur = conn.cursor()
            cur.execute(sqlite_sql, params)
            
            last_id = cur.lastrowid
            row_count = cur.rowcount
            
            if commit:
                conn.commit()
            
            if fetchone:
                row = cur.fetchone()
                return dict(row) if row else None
            elif fetch:
                rows = cur.fetchall()
                return [dict(r) for r in rows]
            
            return {"lastrowid": last_id, "rowcount": row_count}
        
        else: # MySQL
            with conn.cursor() as cur:
                cur.execute(sql, params)
                last_id = cur.lastrowid
                row_count = cur.rowcount
                
                if commit:
                    conn.commit()
                
                if fetchone:
                    return cur.fetchone()
                elif fetch:
                    return cur.fetchall()
                
                return {"lastrowid": last_id, "rowcount": row_count}
    finally:
        conn.close()

def init_database(force_reseed=False):
    """
    Initializes database schema and populates sample records if tables are empty.
    """
    conn = get_connection()
    backend = _ACTIVE_BACKEND
    
    try:
        if backend == "sqlite":
            cur = conn.cursor()
            # 1. Poles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS poles (
                    pole_id TEXT PRIMARY KEY,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    installation_date TEXT,
                    status TEXT DEFAULT 'Normal'
                )
            """)
            
            # 2. Inspections table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pole_id TEXT NOT NULL,
                    inspection_date TEXT DEFAULT (datetime('now', 'localtime')),
                    image_path TEXT NOT NULL,
                    defect_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    severity TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    status TEXT DEFAULT 'Pending Review',
                    FOREIGN KEY (pole_id) REFERENCES poles(pole_id) ON DELETE CASCADE
                )
            """)
            
            # 3. Maintenance table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS maintenance (
                    maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NULL,
                    pole_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    assigned_to TEXT,
                    maintenance_date TEXT DEFAULT (datetime('now', 'localtime')),
                    status TEXT DEFAULT 'Pending',
                    remarks TEXT,
                    FOREIGN KEY (pole_id) REFERENCES poles(pole_id) ON DELETE CASCADE,
                    FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id) ON DELETE SET NULL
                )
            """)
            conn.commit()
            
            # Only seed dummy records if explicitly forced (force_reseed=True)
            if force_reseed:
                logger.info("[DATABASE] Force reseed requested: seeding initial demo poles and inspections...")
                
                sample_poles = [
                    ('P-001', 13.0827, 80.2707, '2021-03-15', 'Normal'),
                    ('P-002', 13.0842, 80.2721, '2020-08-10', 'Warning'),
                    ('P-003', 13.0858, 80.2735, '2022-01-20', 'Normal'),
                    ('P-104', 13.0875, 80.2750, '2019-11-05', 'Critical'),
                    ('P-105', 13.0890, 80.2766, '2021-06-18', 'Normal'),
                    ('P-106', 13.0905, 80.2782, '2020-02-14', 'Critical')
                ]
                cur.executemany(
                    "INSERT OR REPLACE INTO poles (pole_id, latitude, longitude, installation_date, status) VALUES (?, ?, ?, ?, ?)",
                    sample_poles
                )
                
                sample_inspections = [
                    (1, 'P-001', '2026-09-10 10:15:00', 'static/uploads/inspections/sample_good_1.jpg', 'Good Insulator', 96.50, 'LOW', 'Continue regular monitoring.', 'Completed'),
                    (2, 'P-002', '2026-09-12 14:30:00', 'static/uploads/inspections/sample_corrosion.jpg', 'Corrosion / Rust', 87.40, 'MEDIUM', 'Schedule maintenance inspection.', 'Action Required'),
                    (3, 'P-003', '2026-09-15 09:45:00', 'static/uploads/inspections/sample_good_2.jpg', 'Good Insulator', 98.20, 'LOW', 'Continue regular monitoring.', 'Completed'),
                    (4, 'P-104', '2026-09-20 11:20:00', 'static/uploads/inspections/sample_broken_1.jpg', 'Broken Insulator', 94.20, 'HIGH', 'Immediate inspection and replacement recommended.', 'Action Required'),
                    (5, 'P-106', '2026-09-22 16:05:00', 'static/uploads/inspections/sample_flashover_1.jpg', 'Flashover/Damaged Insulator', 92.80, 'HIGH', 'Immediate inspection and replacement recommended.', 'Action Required')
                ]
                cur.executemany(
                    "INSERT OR REPLACE INTO inspections (inspection_id, pole_id, inspection_date, image_path, defect_type, confidence, severity, recommendation, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    sample_inspections
                )
                
                sample_maintenance = [
                    (1, 4, 'P-104', 'Insulator disk replacement & string alignment', 'Marcus Vance (Field Lead)', '2026-09-21 08:30:00', 'Pending', 'Critical broken insulator on lower cross-arm. High risk of line trip.'),
                    (2, 2, 'P-002', 'Cross-arm bracket anti-corrosion coating & bolt tightening', 'Sarah Jenkins', '2026-09-13 13:00:00', 'In Progress', 'Hardware cleaning underway. Coating planned for tomorrow morning.'),
                    (3, 1, 'P-001', 'Annual clearance and vegetation trimming', 'Team Alpha', '2026-09-11 15:00:00', 'Repaired', 'Clearance verified at 3.5m around lines.'),
                    (4, 5, 'P-106', 'Flashover arc damage assessment and ceramic disk replacement', 'David Kim', '2026-09-23 09:15:00', 'Assigned', 'Dispatched technician with bucket truck.')
                ]
                cur.executemany(
                    "INSERT OR REPLACE INTO maintenance (maintenance_id, inspection_id, pole_id, action, assigned_to, maintenance_date, status, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    sample_maintenance
                )
                conn.commit()
                logger.info("[DATABASE] Sample data successfully seeded into SQLite.")
            else:
                logger.info("[DATABASE] Database initialized with clean tables (ready for real inspection data).")
        
        else: # MySQL backend
            with conn.cursor() as cur:
                schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
                if os.path.exists(schema_path):
                    with open(schema_path, "r", encoding="utf-8") as f:
                        sql_commands = f.read().split(";")
                        for cmd in sql_commands:
                            cmd = cmd.strip()
                            if cmd:
                                cur.execute(cmd)
                    conn.commit()
                    logger.info("[DATABASE] schema.sql executed successfully on MySQL.")
    finally:
        conn.close()
