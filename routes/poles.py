from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import execute_query

poles_bp = Blueprint("poles", __name__)

@poles_bp.route("/poles", methods=["GET"])
def list_poles():
    """Renders the poles listing page with search, status filters, and summary metrics."""
    status_filter = request.args.get("status", "").strip()
    search_query = request.args.get("q", "").strip()
    
    query = "SELECT * FROM poles WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
        
    if search_query:
        query += " AND pole_id LIKE %s"
        params.append(f"%{search_query}%")
        
    query += " ORDER BY pole_id ASC"
    poles = execute_query(query, params)
    
    # Calculate summary numbers
    all_poles = execute_query("SELECT status FROM poles")
    total_count = len(all_poles)
    normal_count = sum(1 for p in all_poles if p.get("status") == "Normal")
    warning_count = sum(1 for p in all_poles if p.get("status") == "Warning")
    critical_count = sum(1 for p in all_poles if p.get("status") == "Critical")
    
    return render_template(
        "poles.html",
        poles=poles,
        status_filter=status_filter,
        search_query=search_query,
        total_count=total_count,
        normal_count=normal_count,
        warning_count=warning_count,
        critical_count=critical_count
    )

@poles_bp.route("/poles/<pole_id>", methods=["GET"])
def pole_history(pole_id):
    """
    Displays comprehensive pole history:
    - Pole ID and location coordinates
    - Current status
    - Inspection history with defect tags and annotated images
    - Previous maintenance tasks
    - Latest inspection and latest recommendation
    """
    pole = execute_query("SELECT * FROM poles WHERE pole_id = %s", (pole_id,), fetchone=True)
    if not pole:
        flash(f"Pole '{pole_id}' not found.", "danger")
        return redirect(url_for("poles.list_poles"))
        
    # Get all inspections for this pole, ordered latest first
    inspections = execute_query(
        "SELECT * FROM inspections WHERE pole_id = %s ORDER BY inspection_date DESC",
        (pole_id,)
    )
    
    # Get all maintenance records for this pole
    maintenance_records = execute_query(
        "SELECT * FROM maintenance WHERE pole_id = %s ORDER BY maintenance_date DESC",
        (pole_id,)
    )
    
    # Identify latest inspection and recommendation
    latest_inspection = inspections[0] if inspections else None
    latest_recommendation = (
        latest_inspection["recommendation"]
        if latest_inspection
        else "No prior inspections recorded. Regular scheduled inspection recommended."
    )
    
    return render_template(
        "history.html",
        pole=pole,
        inspections=inspections,
        maintenance_records=maintenance_records,
        latest_inspection=latest_inspection,
        latest_recommendation=latest_recommendation
    )

@poles_bp.route("/poles/add", methods=["POST"])
def add_pole():
    """Adds a new pole asset to the database."""
    pole_id = request.form.get("pole_id", "").strip().upper()
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    installation_date = request.form.get("installation_date", "").strip()
    status = request.form.get("status", "Normal").strip()
    
    if not pole_id or not latitude or not longitude:
        flash("Pole ID, Latitude, and Longitude are required.", "danger")
        return redirect(url_for("poles.list_poles"))
        
    try:
        lat = float(latitude)
        lng = float(longitude)
    except ValueError:
        flash("Latitude and Longitude must be valid numerical coordinates.", "danger")
        return redirect(url_for("poles.list_poles"))
        
    # Check if pole_id already exists
    existing = execute_query("SELECT pole_id FROM poles WHERE pole_id = %s", (pole_id,), fetchone=True)
    if existing:
        flash(f"Pole ID '{pole_id}' already exists in inventory.", "warning")
        return redirect(url_for("poles.list_poles"))
        
    execute_query(
        "INSERT INTO poles (pole_id, latitude, longitude, installation_date, status) VALUES (%s, %s, %s, %s, %s)",
        (pole_id, lat, lng, installation_date or None, status),
        commit=True
    )
    flash(f"Pole {pole_id} successfully added.", "success")
    return redirect(url_for("poles.list_poles"))

@poles_bp.route("/api/poles", methods=["GET"])
def api_get_poles():
    """API endpoint returning pole IDs for search autocomplete and QR verification."""
    poles = execute_query("SELECT pole_id, status, latitude, longitude FROM poles ORDER BY pole_id ASC")
    return jsonify(poles)

@poles_bp.route("/api/poles/<pole_id>", methods=["GET"])
def api_get_pole(pole_id):
    """API endpoint returning specific pole details including location and status."""
    pole = execute_query(
        "SELECT pole_id, latitude, longitude, installation_date, status FROM poles WHERE pole_id = %s",
        (pole_id.strip().upper(),),
        fetchone=True
    )
    if pole:
        return jsonify({"success": True, "pole": pole})
    return jsonify({"success": False, "message": "Pole not found"}), 404

