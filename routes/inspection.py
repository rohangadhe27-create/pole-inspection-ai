import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from config import Config
from database.db import execute_query
from ai.detector import detector

inspection_bp = Blueprint("inspection", __name__)

def allowed_file(filename):
    """Validates that uploaded file has an approved image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@inspection_bp.route("/inspection/new", methods=["GET"])
def new_inspection():
    """Renders the New Inspection workflow page."""
    prefill_pole_id = request.args.get("pole_id", "")
    poles = execute_query("SELECT pole_id, status, latitude, longitude FROM poles ORDER BY pole_id ASC")
    
    return render_template(
        "inspection.html",
        poles=poles,
        prefill_pole_id=prefill_pole_id,
        defect_classes=Config.DEFECT_CLASSES,
        is_demo_mode=(not detector.is_custom_model)
    )

@inspection_bp.route("/inspection/analyze", methods=["POST"])
def analyze_image():
    """
    Handles image upload and triggers YOLO / AI defect detection.
    Returns detection results, severity, recommendations, and annotated image path.
    """
    try:
        pole_id = request.form.get("pole_id", "").strip().upper()
        if not pole_id:
            return jsonify({"success": False, "error": "Pole ID is required."}), 400
            
        force_defect = request.form.get("force_defect", "").strip() or None
        
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image file provided."}), 400
            
        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected."}), 400
            
        if not allowed_file(file.filename):
            allowed = ", ".join(Config.ALLOWED_EXTENSIONS)
            return jsonify({"success": False, "error": f"Invalid file format. Allowed: {allowed}"}), 400
            
        # Ensure directories exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.ANNOTATED_FOLDER, exist_ok=True)
        
        # Save uploaded image with unique secure filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"insp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"
        saved_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        file.save(saved_path)
        
        # Run AI detection via detector module
        result = detector.predict(saved_path, pole_id=pole_id, force_defect=force_defect)
        
        # Web-accessible URLs
        original_url = f"/static/uploads/inspections/{unique_name}"
        annotated_url = result["annotated_image_path"]
        
        # Retrieve pole information if registered
        pole_info = execute_query(
            "SELECT pole_id, latitude, longitude, installation_date, status FROM poles WHERE pole_id = %s",
            (pole_id,),
            fetchone=True
        )
        
        return jsonify({
            "success": True,
            "pole_id": pole_id,
            "pole_info": pole_info,
            "original_image_path": original_url,
            "annotated_image_path": annotated_url,
            "defect_type": result["defect_type"],
            "confidence": result["confidence"],
            "severity": result["severity"],
            "recommendation": result["recommendation"],
            "bbox": result["bbox"],
            "is_demo_mode": result["is_demo_mode"],
            "model_source": result["model_source"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500

@inspection_bp.route("/inspection/save", methods=["POST"])
def save_inspection():
    """
    Saves verified inspection to database and updates pole status.
    Auto-generates a maintenance order if high/critical defect is detected.
    """
    try:
        data = request.get_json() if request.is_json else request.form
        
        pole_id = data.get("pole_id", "").strip().upper()
        image_path = data.get("annotated_image_path") or data.get("original_image_path", "")
        defect_type = data.get("defect_type", "").strip()
        confidence = float(data.get("confidence", 0.0))
        severity = data.get("severity", "LOW").strip().upper()
        recommendation = data.get("recommendation", "").strip()
        
        if not pole_id or not defect_type or not image_path:
            return jsonify({"success": False, "error": "Missing required inspection fields."}), 400
            
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        
        # Ensure pole exists in database
        pole = execute_query("SELECT pole_id, latitude, longitude FROM poles WHERE pole_id = %s", (pole_id,), fetchone=True)
        if not pole:
            # Auto-register new pole with provided coordinates or standard default coordinates
            lat_val = float(latitude) if latitude is not None and str(latitude).strip() != "" else 13.0827
            lng_val = float(longitude) if longitude is not None and str(longitude).strip() != "" else 80.2707
            execute_query(
                "INSERT INTO poles (pole_id, latitude, longitude, status) VALUES (%s, %s, %s, %s)",
                (pole_id, lat_val, lng_val, "Normal"),
                commit=True
            )
        elif latitude is not None and longitude is not None and str(latitude).strip() != "" and str(longitude).strip() != "":
            # Update coordinates if provided explicitly
            try:
                execute_query(
                    "UPDATE poles SET latitude = %s, longitude = %s WHERE pole_id = %s",
                    (float(latitude), float(longitude), pole_id),
                    commit=True
                )
            except (ValueError, TypeError):
                pass
            
        # Set inspection status
        insp_status = "Action Required" if severity in ["HIGH", "CRITICAL", "MEDIUM"] else "Completed"
        
        # Strip leading slash if stored as static path
        clean_img_path = image_path.lstrip("/")
        
        # Insert inspection record
        res = execute_query(
            """
            INSERT INTO inspections 
            (pole_id, image_path, defect_type, confidence, severity, recommendation, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (pole_id, clean_img_path, defect_type, confidence, severity, recommendation, insp_status),
            commit=True
        )
        
        inspection_id = res.get("lastrowid")
        
        # Update pole asset status
        new_pole_status = "Normal"
        if severity == "HIGH":
            new_pole_status = "Critical"
        elif severity == "MEDIUM":
            new_pole_status = "Warning"
            
        execute_query(
            "UPDATE poles SET status = %s WHERE pole_id = %s",
            (new_pole_status, pole_id),
            commit=True
        )
        
        # If high or medium defect, auto-create a maintenance entry
        maint_id = None
        if severity in ["HIGH", "MEDIUM"]:
            action = f"Inspect and replace/repair {defect_type}"
            m_res = execute_query(
                """
                INSERT INTO maintenance (inspection_id, pole_id, action, assigned_to, status, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    inspection_id,
                    pole_id,
                    action,
                    "Unassigned (Auto-Generated)",
                    "Pending",
                    f"Generated from AI inspection #{inspection_id} with severity {severity}."
                ),
                commit=True
            )
            maint_id = m_res.get("lastrowid")
            
        return jsonify({
            "success": True,
            "message": f"Inspection saved successfully for Pole {pole_id}.",
            "inspection_id": inspection_id,
            "maintenance_id": maint_id,
            "pole_status": new_pole_status
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save inspection: {str(e)}"}), 500

@inspection_bp.route("/inspections", methods=["GET"])
def list_inspections():
    """Renders comprehensive list of all past inspections with filters."""
    severity_filter = request.args.get("severity", "").strip().upper()
    defect_filter = request.args.get("defect", "").strip()
    pole_filter = request.args.get("pole_id", "").strip().upper()
    
    query = """
        SELECT i.*, p.latitude, p.longitude, p.status as pole_status 
        FROM inspections i 
        JOIN poles p ON i.pole_id = p.pole_id 
        WHERE 1=1
    """
    params = []
    
    if severity_filter:
        query += " AND i.severity = %s"
        params.append(severity_filter)
        
    if defect_filter:
        query += " AND i.defect_type = %s"
        params.append(defect_filter)
        
    if pole_filter:
        query += " AND i.pole_id = %s"
        params.append(pole_filter)
        
    query += " ORDER BY i.inspection_date DESC"
    inspections = execute_query(query, params)
    
    return render_template(
        "inspections.html",
        inspections=inspections,
        severity_filter=severity_filter,
        defect_filter=defect_filter,
        pole_filter=pole_filter,
        defect_classes=Config.DEFECT_CLASSES
    )

@inspection_bp.route("/defects", methods=["GET"])
def list_defects():
    """Renders dedicated defects board filtered for actionable defects (Broken, Flashover, Corrosion)."""
    defects = execute_query(
        """
        SELECT i.*, p.status as pole_status, p.latitude, p.longitude 
        FROM inspections i
        JOIN poles p ON i.pole_id = p.pole_id
        WHERE i.defect_type != 'Good Insulator'
        ORDER BY 
            CASE i.severity 
                WHEN 'HIGH' THEN 1 
                WHEN 'MEDIUM' THEN 2 
                ELSE 3 
            END,
            i.inspection_date DESC
        """
    )
    
    critical_defects = [d for d in defects if d["severity"] == "HIGH"]
    warning_defects = [d for d in defects if d["severity"] == "MEDIUM"]
    
    return render_template(
        "defects.html",
        defects=defects,
        critical_defects=critical_defects,
        warning_defects=warning_defects
    )
