"""
YOLOv8n Training Script for CPLID Insulator Defect Detection
=============================================================
Trains a YOLOv8 nano model on the prepared CPLID dataset.
- Detects: insulator (class 0), defect (class 1)
- Uses GPU if CUDA is available, else CPU
- Saves best.pt to F:/pole with ai/model/best.pt
"""

import os
import shutil
import time
import glob
from pathlib import Path
import torch
from ultralytics import YOLO

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
PROJECT_DIR   = Path("F:/pole with ai")
DATA_YAML     = PROJECT_DIR / "datasets" / "cplid_yolo" / "data.yaml"
RUNS_DIR      = PROJECT_DIR / "runs" / "detect"
RUN_NAME      = "cplid_yolov8"
BEST_PT_DEST  = PROJECT_DIR / "model" / "best.pt"

EPOCHS    = 50
IMGSZ     = 640
PATIENCE  = 10

# ─────────────────────────────────────────
# Device Selection
# ─────────────────────────────────────────
if torch.cuda.is_available():
    DEVICE = 0          # CUDA GPU 0
    BATCH  = 16         # safe for most 4–8 GB VRAM cards
    print(f"[INFO] GPU detected: {torch.cuda.get_device_name(0)}")
    print(f"[INFO] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    if vram < 4:
        BATCH = 8
    elif vram >= 8:
        BATCH = 32
else:
    DEVICE = "cpu"
    # CPU: keep batch small to avoid OOM with 16 GB RAM
    BATCH  = 8
    print("[INFO] No GPU detected — training on CPU (this will be slower).")

print(f"[INFO] Device: {DEVICE}  |  Batch size: {BATCH}")
print(f"[INFO] Epochs: {EPOCHS}  |  imgsz: {IMGSZ}  |  patience: {PATIENCE}")
print(f"[INFO] Data YAML: {DATA_YAML}")

# ─────────────────────────────────────────
# Validate dataset exists
# ─────────────────────────────────────────
if not DATA_YAML.exists():
    raise FileNotFoundError(
        f"data.yaml not found at {DATA_YAML}. "
        "Run scripts/prepare_cplid_yolo.py first."
    )

# ─────────────────────────────────────────
# Load YOLOv8n base model
# ─────────────────────────────────────────
model = YOLO("yolov8n.pt")   # downloads nano weights automatically on first run

# ─────────────────────────────────────────
# Train
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("STARTING YOLOV8n TRAINING")
print("=" * 60)

start_time = time.time()

results = model.train(
    data     = str(DATA_YAML),
    epochs   = EPOCHS,
    imgsz    = IMGSZ,
    batch    = BATCH,
    patience = PATIENCE,
    device   = DEVICE,
    project  = str(RUNS_DIR),
    name     = RUN_NAME,
    exist_ok = True,         # overwrite if rerun
    plots    = True,         # save training curves, confusion matrix, etc.
    save     = True,
    workers  = 0,            # avoids DataLoader multiprocessing issues on Windows
    verbose  = True,
)

elapsed = time.time() - start_time
hours   = int(elapsed // 3600)
minutes = int((elapsed % 3600) // 60)
seconds = int(elapsed % 60)
print(f"\n[INFO] Training completed in {hours}h {minutes}m {seconds}s")

# ─────────────────────────────────────────
# Copy best weights to model/best.pt
# ─────────────────────────────────────────
run_dir   = RUNS_DIR / RUN_NAME
best_src  = run_dir / "weights" / "best.pt"

if best_src.exists():
    BEST_PT_DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_src, BEST_PT_DEST)
    print(f"[INFO] Best weights saved to: {BEST_PT_DEST}")
else:
    print(f"[WARNING] best.pt not found at {best_src}")

# ─────────────────────────────────────────
# Print metrics summary
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("TRAINING RESULTS SUMMARY")
print("=" * 60)

try:
    metrics = results.results_dict   # dict of final-epoch metrics
    def m(key, default="N/A"):
        v = metrics.get(key, default)
        return f"{v:.4f}" if isinstance(v, float) else str(v)

    print(f"  Precision  (P):  {m('metrics/precision(B)')}")
    print(f"  Recall     (R):  {m('metrics/recall(B)')}")
    print(f"  mAP@0.50    :   {m('metrics/mAP50(B)')}")
    print(f"  mAP@0.50-95 :   {m('metrics/mAP50-95(B)')}")
    print(f"  Box Loss    :   {m('val/box_loss')}")
    print(f"  Cls Loss    :   {m('val/cls_loss')}")
    print(f"  DFL Loss    :   {m('val/dfl_loss')}")
    print(f"  Training time:  {hours}h {minutes}m {seconds}s")
    print(f"  Device:         {'GPU (CUDA)' if DEVICE != 'cpu' else 'CPU'}")
except Exception as e:
    print(f"[WARNING] Could not read metrics dict: {e}")
    print("  Check CSV at:", run_dir / "results.csv")

# ─────────────────────────────────────────
# List generated artefacts
# ─────────────────────────────────────────
print(f"\n[INFO] All artefacts saved under: {run_dir}")
for f in sorted(run_dir.glob("**/*")):
    if f.is_file():
        print(f"  {f.relative_to(run_dir)}")

print("\n[DONE] Training complete. Next step: run inference validation.")
