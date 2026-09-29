import os
import logging
from flask import Flask, render_template, jsonify
from config import Config
from database.db import init_database, execute_query, get_db_backend
from ai.detector import detector
from routes.poles import poles_bp
from routes.inspection import inspection_bp
from routes.maintenance import maintenance_bp

# Set up clean application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PowerLineAI")

def create_app():
    """Application factory for Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required directories exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.ANNOTATED_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "static", "sample_images"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "model"), exist_ok=True)

    # Initialize Database Schema & Seed Data
    try:
        init_database()
        logger.info(f"Database initialized. Active backend: {get_db_backend().upper()}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Register Blueprints
    app.register_blueprint(poles_bp)
    app.register_blueprint(inspection_bp)
    app.register_blueprint(maintenance_bp)

    @app.context_processor
    def inject_global_template_vars():
        """Injects system status indicators into all templates."""
        return {
            "db_backend": get_db_backend().upper(),
            "ai_mode": "Custom YOLO (best.pt)" if detector.is_custom_model else "Demo AI Simulation",
            "is_demo_mode": not detector.is_custom_model,
            "defect_classes": Config.DEFECT_CLASSES,
            "maintenance_stages": Config.MAINTENANCE_STAGES
        }

    @app.route("/", methods=["GET"])
    def dashboard():
        """
        Main Dashboard:
        - Summary KPIs: Total poles, total inspections, total defects, critical defects, normal poles
        - Defect distribution data for Chart.js
        - Pole status distribution data for Chart.js
        - Maintenance workflow breakdown for Chart.js
        - Recent inspections and urgent maintenance tasks
        """
        # Retrieve all poles
        poles = execute_query("SELECT * FROM poles")
        total_poles = len(poles)
        normal_poles = sum(1 for p in poles if p.get("status") == "Normal")
        warning_poles = sum(1 for p in poles if p.get("status") == "Warning")
        critical_poles = sum(1 for p in poles if p.get("status") == "Critical")

        # Retrieve all inspections
        inspections = execute_query("SELECT * FROM inspections ORDER BY inspection_date DESC")
        total_inspections = len(inspections)
        total_defects = sum(1 for i in inspections if i.get("defect_type") != "Good Insulator")
        critical_defects = sum(1 for i in inspections if i.get("severity") == "HIGH")

        # Retrieve maintenance records
        maintenance = execute_query(
            """
            SELECT m.*, p.status as pole_status 
            FROM maintenance m 
            JOIN poles p ON m.pole_id = p.pole_id 
            ORDER BY m.maintenance_id DESC
            """
        )
        pending_maintenance = sum(1 for m in maintenance if m.get("status") in ["Pending", "Assigned", "In Progress"])

        # Defect Distribution for Chart.js
        defect_counts = {}
        for i in inspections:
            dt = i.get("defect_type", "Unknown")
            defect_counts[dt] = defect_counts.get(dt, 0) + 1

        # Defect chart data labels and counts
        defect_labels = list(defect_counts.keys())
        defect_data = [defect_counts[k] for k in defect_labels]

        # Pole status counts for Chart.js
        pole_status_labels = ["Normal", "Warning", "Critical"]
        pole_status_data = [normal_poles, warning_poles, critical_poles]

        # Maintenance stage counts for Chart.js
        maint_counts = {stage: 0 for stage in Config.MAINTENANCE_STAGES}
        for m in maintenance:
            st = m.get("status", "Pending")
            if st in maint_counts:
                maint_counts[st] += 1
        maint_labels = list(maint_counts.keys())
        maint_data = [maint_counts[k] for k in maint_labels]

        return render_template(
            "dashboard.html",
            total_poles=total_poles,
            total_inspections=total_inspections,
            total_defects=total_defects,
            critical_defects=critical_defects,
            normal_poles=normal_poles,
            warning_poles=warning_poles,
            critical_poles=critical_poles,
            pending_maintenance=pending_maintenance,
            recent_inspections=inspections[:6],
            recent_maintenance=maintenance[:6],
            defect_labels=defect_labels,
            defect_data=defect_data,
            pole_status_labels=pole_status_labels,
            pole_status_data=pole_status_data,
            maint_labels=maint_labels,
            maint_data=maint_data
        )

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html", error=str(e)), 500

    return app

if __name__ == "__main__":
    app = create_app()
    # Run locally on port 5000
    app.run(host="127.0.0.1", port=5000, debug=True)
