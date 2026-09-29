"""
CPLID to YOLOv8 Dataset Converter & Validator
=============================================
This script converts the Chinese Power Line Insulator Dataset (CPLID)
from Pascal VOC XML format to standardized YOLOv8 format with stratified
train/validation splits (80/20) while keeping the original dataset untouched.

Class mapping:
  0: insulator
  1: defect
"""

import os
import glob
import shutil
import random
import xml.etree.ElementTree as ET
from PIL import Image
from pathlib import Path

# Paths
BASE_DIR = Path("F:/pole with ai")
CPLID_DIR = BASE_DIR / "CPLID" / "InsulatorDataSet-master" / "InsulatorDataSet-master"
OUTPUT_DIR = BASE_DIR / "datasets" / "cplid_yolo"

NORMAL_IMG_DIR = CPLID_DIR / "Normal_Insulators" / "images"
NORMAL_XML_DIR = CPLID_DIR / "Normal_Insulators" / "labels"

DEFECT_IMG_DIR = CPLID_DIR / "Defective_Insulators" / "images"
DEFECT_DEF_XML_DIR = CPLID_DIR / "Defective_Insulators" / "labels" / "defect"
DEFECT_INS_XML_DIR = CPLID_DIR / "Defective_Insulators" / "labels" / "insulator"

CLASS_MAP = {
    "insulator": 0,
    "defect": 1
}

def parse_voc_xml(xml_path, img_path):
    """
    Parses Pascal VOC XML, extracts actual image dimensions from XML (fallback to image file),
    and converts bounding boxes to YOLO normalized coordinates [class_id, x_center, y_center, width, height].
    """
    if not os.path.exists(xml_path):
        return []
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Extract dimensions from XML
    size_elem = root.find("size")
    width = 0
    height = 0
    if size_elem is not None:
        w_elem = size_elem.find("width")
        h_elem = size_elem.find("height")
        if w_elem is not None and h_elem is not None:
            width = float(w_elem.text)
            height = float(h_elem.text)
    
    # Fallback to reading actual image dimensions if missing in XML
    if width <= 0 or height <= 0:
        with Image.open(img_path) as im:
            width, height = im.size
            
    boxes = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip().lower()
        if name not in CLASS_MAP:
            continue
        
        class_id = CLASS_MAP[name]
        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)
        
        # Clamp coordinates to image boundaries
        xmin = max(0.0, min(xmin, width))
        ymin = max(0.0, min(ymin, height))
        xmax = max(0.0, min(xmax, width))
        ymax = max(0.0, min(ymax, height))
        
        box_w = xmax - xmin
        box_h = ymax - ymin
        
        if box_w <= 0 or box_h <= 0:
            continue
            
        x_center = (xmin + xmax) / (2.0 * width)
        y_center = (ymin + ymax) / (2.0 * height)
        norm_w = box_w / width
        norm_h = box_h / height
        
        # Ensure values stay strictly in [0.0, 1.0]
        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        norm_w = min(max(norm_w, 0.0), 1.0)
        norm_h = min(max(norm_h, 0.0), 1.0)
        
        boxes.append((class_id, x_center, y_center, norm_w, norm_h))
        
    return boxes

def prepare_dataset():
    print("=" * 70)
    print("STARTING CPLID TO YOLOV8 DATASET PREPARATION")
    print("=" * 70)
    
    # Ensure source directory exists
    if not CPLID_DIR.exists():
        raise FileNotFoundError(f"Source CPLID dataset directory not found at: {CPLID_DIR}")
        
    # Create target directory structure
    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
        
    print(f"Target directory initialized: {OUTPUT_DIR}")
    
    # 1. Gather Normal Insulator pairs
    normal_img_files = sorted(glob.glob(str(NORMAL_IMG_DIR / "*.jpg")))
    print(f"Found {len(normal_img_files)} normal insulator images.")
    
    normal_samples = []
    for img_p in normal_img_files:
        base_name = os.path.splitext(os.path.basename(img_p))[0]
        xml_p = str(NORMAL_XML_DIR / f"{base_name}.xml")
        boxes = parse_voc_xml(xml_p, img_p)
        normal_samples.append({
            "img_path": img_p,
            "filename": os.path.basename(img_p),
            "label_filename": f"{base_name}.txt",
            "boxes": boxes,
            "category": "normal"
        })
        
    # 2. Gather Defective Insulator pairs (merge insulator and defect XMLs)
    defective_img_files = sorted(glob.glob(str(DEFECT_IMG_DIR / "*.jpg")))
    print(f"Found {len(defective_img_files)} defective insulator images.")
    
    defective_samples = []
    for img_p in defective_img_files:
        base_name = os.path.splitext(os.path.basename(img_p))[0]
        xml_def = str(DEFECT_DEF_XML_DIR / f"{base_name}.xml")
        xml_ins = str(DEFECT_INS_XML_DIR / f"{base_name}.xml")
        
        boxes_def = parse_voc_xml(xml_def, img_p)
        boxes_ins = parse_voc_xml(xml_ins, img_p)
        merged_boxes = boxes_ins + boxes_def
        
        defective_samples.append({
            "img_path": img_p,
            "filename": os.path.basename(img_p),
            "label_filename": f"{base_name}.txt",
            "boxes": merged_boxes,
            "category": "defective"
        })
        
    # 3. Perform Stratified 80/20 Split
    random.seed(42)
    random.shuffle(normal_samples)
    random.shuffle(defective_samples)
    
    # Normal: 480 train / 120 val (80% / 20%)
    norm_split_idx = int(len(normal_samples) * 0.8) # 480
    norm_train = normal_samples[:norm_split_idx]
    norm_val = normal_samples[norm_split_idx:]
    
    # Defective: 198 train / 50 val (80% / 20%)
    def_split_idx = int(len(defective_samples) * 0.8) # 198
    def_train = defective_samples[:def_split_idx]
    def_val = defective_samples[def_split_idx:]
    
    train_dataset = norm_train + def_train
    val_dataset = norm_val + def_val
    
    print(f"\nStratified Split Summary:")
    print(f"  - Train: {len(norm_train)} normal + {len(def_train)} defective = {len(train_dataset)} images")
    print(f"  - Val:   {len(norm_val)} normal + {len(def_val)} defective = {len(val_dataset)} images")
    print(f"  - Total: {len(train_dataset) + len(val_dataset)} images")
    
    # 4. Copy images and write YOLO labels
    def write_split(samples, split_name):
        dest_img_dir = OUTPUT_DIR / "images" / split_name
        dest_lbl_dir = OUTPUT_DIR / "labels" / split_name
        
        for sample in samples:
            # Copy image (preserves original)
            dest_img = dest_img_dir / sample["filename"]
            shutil.copy2(sample["img_path"], dest_img)
            
            # Write YOLO label txt
            dest_lbl = dest_lbl_dir / sample["label_filename"]
            with open(dest_lbl, "w", encoding="utf-8") as f:
                for box in sample["boxes"]:
                    cid, xc, yc, bw, bh = box
                    f.write(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                    
    print("\nCopying images and writing YOLO annotation files...")
    write_split(train_dataset, "train")
    write_split(val_dataset, "val")
    print("Files successfully generated.")
    
    # 5. Generate data.yaml
    yaml_content = f"""path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val
names:
  0: insulator
  1: defect
"""
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
        
    print(f"\nYOLO data.yaml written to: {yaml_path}")
    
    # 6. Validate the entire prepared dataset
    validate_dataset()

def validate_dataset():
    print("\n" + "=" * 70)
    print("VALIDATING YOLOV8 DATASET INTEGRITY")
    print("=" * 70)
    
    errors = []
    stats = {
        "train_images": 0,
        "val_images": 0,
        "train_labels": 0,
        "val_labels": 0,
        "insulator_objects": 0,
        "defect_objects": 0,
        "train_insulators": 0,
        "train_defects": 0,
        "val_insulators": 0,
        "val_defects": 0
    }
    
    for split in ["train", "val"]:
        img_dir = OUTPUT_DIR / "images" / split
        lbl_dir = OUTPUT_DIR / "labels" / split
        
        images = sorted(glob.glob(str(img_dir / "*.jpg")))
        labels = sorted(glob.glob(str(lbl_dir / "*.txt")))
        
        stats[f"{split}_images"] = len(images)
        stats[f"{split}_labels"] = len(labels)
        
        img_basenames = {os.path.splitext(os.path.basename(f))[0] for f in images}
        lbl_basenames = {os.path.splitext(os.path.basename(f))[0] for f in labels}
        
        # Check matching 1:1 image and label
        missing_labels = img_basenames - lbl_basenames
        missing_images = lbl_basenames - img_basenames
        
        if missing_labels:
            errors.append(f"Split [{split}]: {len(missing_labels)} images missing label files!")
        if missing_images:
            errors.append(f"Split [{split}]: {len(missing_images)} labels missing image files!")
            
        # Validate coordinates and classes in every label file
        for lbl_path in labels:
            with open(lbl_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            if len(lines) == 0:
                errors.append(f"Empty label file: {lbl_path}")
                
            for idx, line in enumerate(lines, 1):
                parts = line.strip().split()
                if len(parts) != 5:
                    errors.append(f"Invalid format in {lbl_path} line {idx}: {line.strip()}")
                    continue
                    
                cls_str, xc_str, yc_str, w_str, h_str = parts
                try:
                    cls_id = int(cls_str)
                    xc = float(xc_str)
                    yc = float(yc_str)
                    w = float(w_str)
                    h = float(h_str)
                except ValueError:
                    errors.append(f"Non-numeric values in {lbl_path} line {idx}: {line.strip()}")
                    continue
                    
                if cls_id not in [0, 1]:
                    errors.append(f"Invalid class ID {cls_id} in {lbl_path} line {idx}")
                    
                if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0):
                    errors.append(f"Coordinates out of [0, 1] bounds in {lbl_path} line {idx}: {line.strip()}")
                    
                if cls_id == 0:
                    stats["insulator_objects"] += 1
                    stats[f"{split}_insulators"] += 1
                elif cls_id == 1:
                    stats["defect_objects"] += 1
                    stats[f"{split}_defects"] += 1
                    
    print("\n--- VALIDATION RESULTS ---")
    print(f"Number of train images:       {stats['train_images']}")
    print(f"Number of validation images:  {stats['val_images']}")
    print(f"Number of train labels:       {stats['train_labels']}")
    print(f"Number of validation labels:  {stats['val_labels']}")
    print(f"Total images:                 {stats['train_images'] + stats['val_images']}")
    print(f"Total labels:                 {stats['train_labels'] + stats['val_labels']}")
    print(f"Number of insulator objects:  {stats['insulator_objects']} (Train: {stats['train_insulators']}, Val: {stats['val_insulators']})")
    print(f"Number of defect objects:     {stats['defect_objects']} (Train: {stats['train_defects']}, Val: {stats['val_defects']})")
    print(f"Total object instances:       {stats['insulator_objects'] + stats['defect_objects']}")
    
    if errors:
        print(f"\nVALIDATION STATUS: FAILED ({len(errors)} errors found)")
        for err in errors[:10]:
            print(f"  - {err}")
    else:
        print("\nVALIDATION STATUS: PASSED (100% Valid YOLOv8 Dataset, Zero Errors)")
    print("=" * 70)

if __name__ == "__main__":
    prepare_dataset()
