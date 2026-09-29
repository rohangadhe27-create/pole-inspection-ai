import os
import unittest
import json
from io import BytesIO
from app import create_app
from database.db import execute_query

class TestPowerLineAI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_01_dashboard_loads(self):
        """Test operational dashboard route."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GridSense AI", response.data)
        self.assertIn(b"Total Poles", response.data)
        self.assertIn(b"Defects Detected", response.data)

    def test_02_poles_list(self):
        """Test poles listing and filtering."""
        execute_query("INSERT OR IGNORE INTO poles (pole_id, latitude, longitude, status) VALUES ('P-104', 13.0827, 80.2707, 'Normal')", commit=True)
        response = self.client.get("/poles")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"P-104", response.data)

    def test_03_pole_history(self):
        """Test pole history and latest recommendation for P-104."""
        execute_query("INSERT OR IGNORE INTO poles (pole_id, latitude, longitude, status) VALUES ('P-104', 13.0827, 80.2707, 'Normal')", commit=True)
        execute_query("INSERT INTO inspections (pole_id, image_path, defect_type, confidence, severity, recommendation, status) VALUES ('P-104', 'test.jpg', 'Broken Insulator', 95.0, 'HIGH', 'Immediate inspection and replacement recommended.', 'Action Required')", commit=True)
        response = self.client.get("/poles/P-104")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"P-104", response.data)
        self.assertIn(b"Broken Insulator", response.data)
        self.assertIn(b"Immediate inspection and replacement recommended.", response.data)

    def test_04_inspection_new_page(self):
        """Test new inspection page loads."""
        response = self.client.get("/inspection/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pole Identification", response.data)
        self.assertIn(b"Analyze Image", response.data)

    def test_05_ai_analysis_endpoint(self):
        """Test AI defect analysis on sample broken insulator image."""
        sample_image_path = "static/sample_images/broken_insulator.jpg"
        self.assertTrue(os.path.exists(sample_image_path), "Sample image must exist")

        with open(sample_image_path, "rb") as f:
            img_bytes = f.read()

        data = {
            "pole_id": "P-104",
            "force_defect": "Broken Insulator",
            "image": (BytesIO(img_bytes), "test_broken.jpg")
        }

        response = self.client.post(
            "/inspection/analyze",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["pole_id"], "P-104")
        self.assertEqual(json_data["defect_type"], "Broken Insulator")
        self.assertEqual(json_data["severity"], "HIGH")
        self.assertIn("Immediate inspection and replacement recommended.", json_data["recommendation"])
        self.assertTrue(json_data["annotated_image_path"].startswith("/static/uploads/annotated/"))

    def test_06_save_inspection_and_auto_maintenance(self):
        """Test saving an inspection record and verifying database insertion + auto-maintenance."""
        payload = {
            "pole_id": "P-104",
            "defect_type": "Broken Insulator",
            "confidence": 94.2,
            "severity": "HIGH",
            "recommendation": "Immediate inspection and replacement recommended.",
            "annotated_image_path": "static/uploads/annotated/test_annotated.jpg",
            "original_image_path": "static/uploads/inspections/test_orig.jpg"
        }

        response = self.client.post(
            "/inspection/save",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["inspection_id"])
        self.assertIsNotNone(data["maintenance_id"])

        # Verify pole status updated to Critical
        pole = execute_query("SELECT status FROM poles WHERE pole_id = 'P-104'", fetchone=True)
        self.assertEqual(pole["status"], "Critical")

    def test_07_maintenance_update_workflow(self):
        """Test maintenance workflow progression: Pending -> Assigned -> In Progress -> Repaired."""
        # Create a test maintenance record
        res = execute_query(
            "INSERT INTO maintenance (pole_id, action, status) VALUES ('P-003', 'Hardware tightening', 'Pending')",
            commit=True
        )
        maint_id = res["lastrowid"]

        # Update to In Progress
        post_data = {
            "maintenance_id": maint_id,
            "status": "In Progress",
            "assigned_to": "Technician Mark",
            "remarks": "Partially completed"
        }
        resp = self.client.post("/maintenance/update", data=post_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify status in database
        record = execute_query("SELECT status, assigned_to FROM maintenance WHERE maintenance_id = %s", (maint_id,), fetchone=True)
        self.assertEqual(record["status"], "In Progress")
        self.assertEqual(record["assigned_to"], "Technician Mark")

    def test_08_reports_page(self):
        """Test reports page renders correctly."""
        response = self.client.get("/reports")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Executive Inspection", response.data)
        self.assertIn(b"Resolution Rate", response.data)

if __name__ == "__main__":
    unittest.main()
