# YOLO Model Directory

Place your custom trained YOLO weights here as `best.pt`:

```
model/
└── best.pt
```

### Supported AI Defect Classes:
1. `Good Insulator`
2. `Broken Insulator`
3. `Flashover/Damaged Insulator`

### How It Works:
- When `model/best.pt` exists and is non-empty, the system automatically loads it via `ultralytics.YOLO("model/best.pt")`.
- If `model/best.pt` is not present, the system runs in a clearly-labeled **Demo Mode** using OpenCV overlays and deterministic test scenarios so the entire web prototype, database, and maintenance workflows can still be fully tested and demonstrated.
