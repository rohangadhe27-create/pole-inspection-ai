from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config import Config
from database.db import execute_query

maintenance_bp = Blueprint("maintenance", __name__)

@maintenance_bp.route("/maintenance", methods=["GET"])
def list_maintenance():
    """
    Renders maintenance management page with workflow stage filters
    and task update actions.
    Workflow stages: Pending -> Assigned -> In Progress -> Repaired -> Verified
    """
    status_filter = request.args.get("status", "").strip()
    pole_filter = request.args.get("pole_id", "").strip().upper()
    
    query = """
        SELECT m.*, p.status as pole_status, p.latitude, p.longitude, i.defect_type, i.severity as defect_severity
        FROM maintenance m
        JOIN poles p ON m.pole_id = p.pole_id
        LEFT JOIN inspections i ON m.inspection_id = i.inspection_id
        WHERE 1=1
    """
    params = []
    
    if status_filter:
        query += " AND m.status = %s"
        params.append(status_filter)
        
    if pole_filter:
        query += " AND m.pole_id = %s"
        params.append(pole_filter)
        
    query += " ORDER BY m.maintenance_id DESC"
    records = execute_query(query, params)
    
    # Summary statistics for workflow badges
    all_records = execute_query("SELECT status FROM maintenance")
    counts = {
        "Pending": sum(1 for r in all_records if r.get("status") == "Pending"),
        "Assigned": sum(1 for r in all_records if r.get("status") == "Assigned"),
        "In Progress": sum(1 for r in all_records if r.get("status") == "In Progress"),
        "Repaired": sum(1 for r in all_records if r.get("status") == "Repaired"),
        "Verified": sum(1 for r in all_records if r.get("status") == "Verified"),
    }
    
    poles = execute_query("SELECT pole_id FROM poles ORDER BY pole_id ASC")
    
    return render_template(
        "maintenance.html",
        records=records,
        status_filter=status_filter,
        pole_filter=pole_filter,
        counts=counts,
        stages=Config.MAINTENANCE_STAGES,
        poles=poles
    )

@maintenance_bp.route("/maintenance/update", methods=["POST"])
def update_maintenance():
    """
    Updates the maintenance status, assigned personnel, and notes.
    If repaired/verified, checks if pole status can be reset to Normal.
    """
    maint_id = request.form.get("maintenance_id")
    new_status = request.form.get("status", "").strip()
    assigned_to = request.form.get("assigned_to", "").strip()
    remarks = request.form.get("remarks", "").strip()
    
    if not maint_id or not new_status:
        flash("Maintenance ID and Status are required.", "danger")
        return redirect(url_for("maintenance.list_maintenance"))
        
    # Get current maintenance record to know pole_id
    record = execute_query("SELECT * FROM maintenance WHERE maintenance_id = %s", (maint_id,), fetchone=True)
    if not record:
        flash("Maintenance record not found.", "danger")
        return redirect(url_for("maintenance.list_maintenance"))
        
    pole_id = record["pole_id"]
    
    execute_query(
        """
        UPDATE maintenance 
        SET status = %s, assigned_to = %s, remarks = %s 
        WHERE maintenance_id = %s
        """,
        (new_status, assigned_to or record["assigned_to"], remarks or record["remarks"], maint_id),
        commit=True
    )
    
    # If task is marked Repaired or Verified, check if other open tasks exist for this pole
    if new_status in ["Repaired", "Verified"]:
        pending_tasks = execute_query(
            "SELECT COUNT(*) as count FROM maintenance WHERE pole_id = %s AND status IN ('Pending', 'Assigned', 'In Progress')",
            (pole_id,),
            fetchone=True
        )
        if pending_tasks and (pending_tasks.get("count") or pending_tasks.get("COUNT(*)")) == 0:
            # All maintenance resolved: update pole status to Normal
            execute_query("UPDATE poles SET status = 'Normal' WHERE pole_id = %s", (pole_id,), commit=True)
            flash(f"Maintenance #{maint_id} updated to {new_status}. Pole {pole_id} status restored to 'Normal'.", "success")
            return redirect(url_for("maintenance.list_maintenance"))
            
    flash(f"Maintenance #{maint_id} status successfully updated to {new_status}.", "success")
    return redirect(url_for("maintenance.list_maintenance"))

@maintenance_bp.route("/maintenance/create", methods=["POST"])
def create_maintenance():
    """Manually creates a new maintenance order."""
    pole_id = request.form.get("pole_id", "").strip().upper()
    action = request.form.get("action", "").strip()
    assigned_to = request.form.get("assigned_to", "").strip()
    remarks = request.form.get("remarks", "").strip()
    
    if not pole_id or not action:
        flash("Pole ID and Maintenance Action description are required.", "danger")
        return redirect(url_for("maintenance.list_maintenance"))
        
    execute_query(
        """
        INSERT INTO maintenance (pole_id, action, assigned_to, status, remarks)
        VALUES (%s, %s, %s, 'Pending', %s)
        """,
        (pole_id, action, assigned_to or "Unassigned", remarks),
        commit=True
    )
    
    # Ensure pole status reflects maintenance required
    execute_query(
        "UPDATE poles SET status = CASE WHEN status = 'Critical' THEN 'Critical' ELSE 'Warning' END WHERE pole_id = %s",
        (pole_id,),
        commit=True
    )
    
    flash(f"Maintenance task for Pole {pole_id} successfully created.", "success")
    return redirect(url_for("maintenance.list_maintenance"))

@maintenance_bp.route("/reports", methods=["GET"])
def view_reports():
    """Generates an executive inspection summary and maintenance progress report."""
    poles = execute_query("SELECT * FROM poles")
    inspections = execute_query("SELECT * FROM inspections ORDER BY inspection_date DESC")
    maintenance_records = execute_query("SELECT * FROM maintenance ORDER BY maintenance_date DESC")
    
    total_poles = len(poles)
    total_inspections = len(inspections)
    total_defects = sum(1 for i in inspections if i.get("defect_type") != "Good Insulator")
    critical_defects = sum(1 for i in inspections if i.get("severity") == "HIGH")
    
    resolved_maintenance = sum(1 for m in maintenance_records if m.get("status") in ["Repaired", "Verified"])
    total_maintenance = len(maintenance_records)
    resolution_rate = round((resolved_maintenance / total_maintenance * 100), 1) if total_maintenance > 0 else 100.0
    
    return render_template(
        "reports.html",
        total_poles=total_poles,
        total_inspections=total_inspections,
        total_defects=total_defects,
        critical_defects=critical_defects,
        total_maintenance=total_maintenance,
        resolved_maintenance=resolved_maintenance,
        resolution_rate=resolution_rate,
        recent_inspections=inspections[:10],
        recent_maintenance=maintenance_records[:10]
    )
