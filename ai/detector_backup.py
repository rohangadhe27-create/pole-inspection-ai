import os
import cv2
import numpy as np
import logging
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class DefectDetector:
    """
    AI Defect Detector Module.
    Loads custom trained YOLO weights (e.g., model/best.pt) via Ultralytics.
    If custom trained weights are not detected, it provides a clearly labeled
    Demo/Mock inference mode with realistic defect coordinates and OpenCV annotations
    so the prototype can be fully tested and demonstrated out of the box.
    """
    
    def __init__(self, model_path=None):
        self.model_path = model_path or Config.MODEL_PATH
        self.model = None
        self.is_custom_model = False
        self.ultralytics_available = False
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Attempts to load YOLO model if weights exist."""
        try:
            from ultralytics import YOLO
            self.ultralytics_available = True
            
            if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 1000:
                logger.info(f"[AI MODEL] Loading trained YOLO weights from {self.model_path}")
                self.model = YOLO(self.model_path)
                self.is_custom_model = True
                logger.info("[AI MODEL] Custom YOLO model successfully loaded into memory.")
            else:
                logger.info(
                    f"[AI MODEL] Model weights file '{self.model_path}' not found or empty. "
                    "Operating in clearly-labeled DEMO INFERENCE MODE."
                )
                self.is_custom_model = False
        except ImportError:
            logger.warning("[AI MODEL] Ultralytics package not available. Falling back to Demo mode.")
            self.ultralytics_available = False
            self.is_custom_model = False
        except Exception as e:
            logger.error(f"[AI MODEL] Error initializing YOLO model: {e}. Falling back to Demo mode.")
            self.is_custom_model = False

    def assess_severity(self, defect_type):
        """Maps defect class to severity level (HIGH, MEDIUM, LOW) based on config."""
        return Config.DEFECT_SEVERITY_MAP.get(defect_type, "MEDIUM")

    def get_recommendation(self, severity):
        """Generates operational maintenance recommendation according to severity."""
        return Config.MAINTENANCE_RECOMMENDATIONS.get(
            severity.upper(),
            "Schedule maintenance inspection."
        )

    def predict(self, image_path, pole_id="Unknown", force_defect=None):
        """
        Runs defect detection on an input image.
        
        Args:
            image_path (str): Absolute or relative path to the inspection image.
            pole_id (str): Pole ID for tracking and labeling.
            force_defect (str, optional): In demo mode, allows selecting a specific defect class.
            
        Returns:
            dict: Detection results containing defect_type, confidence, severity,
                  recommendation, bounding box, and annotated image path.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        # Ensure output directory for annotated images exists
        os.makedirs(Config.ANNOTATED_FOLDER, exist_ok=True)
        filename = os.path.basename(image_path)
        annotated_filename = f"annotated_{filename}"
        annotated_path = os.path.join(Config.ANNOTATED_FOLDER, annotated_filename)

        if self.is_custom_model and self.model:
            return self._predict_yolo(image_path, annotated_path, pole_id)
        else:
            return self._predict_demo(image_path, annotated_path, pole_id, force_defect)

    def _predict_yolo(self, image_path, annotated_path, pole_id):
        """Runs actual inference using the loaded YOLO model."""
        try:
            results = self.model(image_path)
            res = results[0]
            
            img = cv2.imread(image_path)
            h, w, _ = img.shape
            
            defect_type = "Good Insulator"
            confidence = 90.0
            bbox = [int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75)]
            
            if len(res.boxes) > 0:
                # Pick the detection with the highest confidence
                box = res.boxes[0]
                cls_idx = int(box.cls[0].item())
                confidence = round(float(box.conf[0].item()) * 100, 1)
                
                # Retrieve class name from model names dictionary
                if hasattr(self.model, "names") and cls_idx in self.model.names:
                    defect_type = self.model.names[cls_idx]
                else:
                    defect_type = Config.DEFECT_CLASSES[cls_idx % len(Config.DEFECT_CLASSES)]
                
                xyxy = box.xyxy[0].tolist()
                bbox = [int(coord) for coord in xyxy]
            
            severity = self.assess_severity(defect_type)
            recommendation = self.get_recommendation(severity)
            
            # Annotate image with OpenCV
            self._draw_annotation(
                image_path=image_path,
                output_path=annotated_path,
                bbox=bbox,
                label=defect_type,
                confidence=confidence,
                severity=severity,
                pole_id=pole_id,
                is_demo=False
            )
            
            return {
                "defect_type": defect_type,
                "confidence": confidence,
                "severity": severity,
                "recommendation": recommendation,
                "bbox": bbox,
                "is_demo_mode": False,
                "model_source": f"YOLO ({os.path.basename(self.model_path)})",
                "annotated_image_path": f"/static/uploads/annotated/{os.path.basename(annotated_path)}"
            }
        except Exception as e:
            logger.error(f"[AI MODEL] Inference failed with custom model: {e}. Falling back to demo mode.")
            return self._predict_demo(image_path, annotated_path, pole_id)

    def _predict_demo(self, image_path, annotated_path, pole_id, force_defect=None):
        """
        Intelligent placeholder/demo inference mode.
        Clearly labeled as DEMO MODE so evaluation is transparent.
        Generates realistic bounding boxes and classifications.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image using OpenCV: {image_path}")
        
        h, w, _ = img.shape
        
        # Determine defect classification
        if force_defect and force_defect in Config.DEFECT_CLASSES:
            defect_type = force_defect
            conf_map = {
                "Broken Insulator": 94.2,
                "Flashover/Damaged Insulator": 91.5,
                "Good Insulator": 97.8
            }
            confidence = conf_map.get(defect_type, 92.0)
        else:
            # Deterministic defect selection based on image name or pole_id
            name_lower = os.path.basename(image_path).lower()
            pole_lower = str(pole_id).lower()
            
            if "broken" in name_lower or "104" in pole_lower:
                defect_type = "Broken Insulator"
                confidence = 94.2
            elif "flashover" in name_lower or "damage" in name_lower or "106" in pole_lower:
                defect_type = "Flashover/Damaged Insulator"
                confidence = 92.8
            elif "corrosion" in name_lower or "002" in pole_lower:
                defect_type = "Broken Insulator"  # Core defect category
                confidence = 88.5
            else:
                defect_type = "Good Insulator"
                confidence = 96.5

        severity = self.assess_severity(defect_type)
        recommendation = self.get_recommendation(severity)

        # Generate realistic bounding box coordinates
        pad_x = int(w * 0.18)
        pad_y = int(h * 0.22)
        bbox = [
            max(0, pad_x),
            max(0, pad_y),
            min(w, w - pad_x),
            min(h, h - pad_y)
        ]

        # Draw OpenCV bounding box and annotations
        self._draw_annotation(
            image_path=image_path,
            output_path=annotated_path,
            bbox=bbox,
            label=defect_type,
            confidence=confidence,
            severity=severity,
            pole_id=pole_id,
            is_demo=True
        )

        return {
            "defect_type": defect_type,
            "confidence": confidence,
            "severity": severity,
            "recommendation": recommendation,
            "bbox": bbox,
            "is_demo_mode": True,
            "model_source": "Demo Mode (Replace model/best.pt with trained YOLO weights)",
            "annotated_image_path": f"/static/uploads/annotated/{os.path.basename(annotated_path)}"
        }

    def _draw_annotation(self, image_path, output_path, bbox, label, confidence, severity, pole_id, is_demo):
        """Annotates image with OpenCV bounding boxes, severity labels, and status badges."""
        img = cv2.imread(image_path)
        x1, y1, x2, y2 = bbox
        
        # Color coding: BGR format
        # Red for HIGH, Orange for MEDIUM, Green for LOW
        if severity == "HIGH":
            box_color = (40, 40, 235)      # Red
            header_color = (25, 25, 200)
        elif severity == "MEDIUM":
            box_color = (0, 165, 255)     # Amber/Orange
            header_color = (0, 140, 220)
        else:
            box_color = (35, 175, 50)      # Green
            header_color = (25, 145, 40)
        
        # 1. Draw main bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)
        
        # Corner accent markers
        corner_len = min(25, int((x2 - x1) * 0.2))
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), box_color, 5)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), box_color, 5)
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), box_color, 5)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), box_color, 5)
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), box_color, 5)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), box_color, 5)
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), box_color, 5)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), box_color, 5)

        # 2. Text label background banner
        text_label = f"{label} | Conf: {confidence:.1f}% | [{severity}]"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(text_label, font, font_scale, thickness)
        
        # Ensure label banner fits inside image boundaries
        banner_y1 = max(0, y1 - text_h - 14)
        banner_y2 = max(text_h + 14, y1)
        banner_x2 = min(img.shape[1], x1 + text_w + 16)
        
        cv2.rectangle(img, (x1, banner_y1), (banner_x2, banner_y2), header_color, -1)
        cv2.putText(
            img, text_label,
            (x1 + 8, banner_y2 - 6),
            font, font_scale,
            (255, 255, 255), thickness, cv2.LINE_AA
        )

        # 3. Pole ID and Top Status Header
        top_banner = f"Pole: {pole_id} | Power Line Inspection AI"
        cv2.rectangle(img, (0, 0), (min(img.shape[1], 450), 32), (30, 30, 30), -1)
        cv2.putText(img, top_banner, (10, 22), font, 0.55, (240, 240, 240), 1, cv2.LINE_AA)

        # 4. If demo mode, include clear indicator badge
        if is_demo:
            demo_tag = "[DEMO INFERENCE MODE]"
            cv2.rectangle(img, (img.shape[1] - 240, 0), (img.shape[1], 30), (0, 100, 200), -1)
            cv2.putText(
                img, demo_tag,
                (img.shape[1] - 230, 20),
                font, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA
            )

        # Save annotated image
        cv2.imwrite(output_path, img)
        return output_path

# Global detector instance
detector = DefectDetector()
