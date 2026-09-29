import os
import cv2
import numpy as np

def create_sample_images():
    os.makedirs("static/uploads/inspections", exist_ok=True)
    os.makedirs("static/uploads/annotated", exist_ok=True)
    os.makedirs("static/sample_images", exist_ok=True)

    def draw_pole_base(w=800, h=600):
        # Create a realistic sky background with slight gradient
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            r = int(120 + (y / h) * 40)
            g = int(170 + (y / h) * 40)
            b = int(220 + (y / h) * 20)
            img[y, :] = (b, g, r)

        # Draw concrete / wooden pole in background
        pole_x = w // 2
        cv2.line(img, (pole_x, h), (pole_x, 150), (90, 100, 110), 45)
        # Cross-arm beam
        cv2.line(img, (pole_x - 220, 200), (pole_x + 220, 200), (70, 75, 80), 22)
        # Power cables
        cv2.line(img, (0, 190), (pole_x - 170, 215), (30, 30, 30), 4)
        cv2.line(img, (pole_x - 170, 215), (pole_x + 170, 215), (30, 30, 30), 4)
        cv2.line(img, (pole_x + 170, 215), (w, 190), (30, 30, 30), 4)
        return img

    # 1. Good Insulator
    good_img = draw_pole_base()
    # Draw intact bell-shaped ceramic insulator discs
    cx, cy = 400, 290
    for i in range(5):
        disc_y = cy + (i * 32)
        cv2.ellipse(good_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (230, 235, 240), -1)
        cv2.ellipse(good_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (140, 150, 160), 2)
    # Connecting pin
    cv2.line(good_img, (cx, 210), (cx, cy + 160), (80, 80, 85), 7)
    cv2.imwrite("static/uploads/inspections/sample_good_1.jpg", good_img)
    cv2.imwrite("static/uploads/inspections/sample_good_2.jpg", good_img)
    cv2.imwrite("static/sample_images/good_insulator.jpg", good_img)

    # 2. Broken Insulator
    broken_img = draw_pole_base()
    cx, cy = 400, 290
    cv2.line(broken_img, (cx, 210), (cx, cy + 160), (80, 80, 85), 7)
    # Intact top discs
    for i in range(2):
        disc_y = cy + (i * 32)
        cv2.ellipse(broken_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (230, 235, 240), -1)
        cv2.ellipse(broken_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (140, 150, 160), 2)
    # Broken discs (jagged chunks missing)
    for i in range(2, 5):
        disc_y = cy + (i * 32)
        # Draw fractured half-disc
        pts = np.array([
            [cx - 42, disc_y], [cx - 10, disc_y - 12], [cx + 15, disc_y + 8],
            [cx + 35, disc_y - 5], [cx + 10, disc_y + 14], [cx - 35, disc_y + 10]
        ], np.int32)
        cv2.fillPoly(broken_img, [pts], (180, 175, 170))
        cv2.polylines(broken_img, [pts], True, (60, 60, 60), 2)
        # crack marks
        cv2.line(broken_img, (cx - 20, disc_y), (cx + 10, disc_y + 10), (40, 30, 30), 2)
    cv2.imwrite("static/uploads/inspections/sample_broken_1.jpg", broken_img)
    cv2.imwrite("static/sample_images/broken_insulator.jpg", broken_img)

    # 3. Flashover / Damaged Insulator
    flashover_img = draw_pole_base()
    cx, cy = 400, 290
    cv2.line(flashover_img, (cx, 210), (cx, cy + 160), (80, 80, 85), 7)
    for i in range(5):
        disc_y = cy + (i * 32)
        cv2.ellipse(flashover_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (210, 215, 220), -1)
        cv2.ellipse(flashover_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (120, 130, 140), 2)
        # Heavy black electrical arc scorch / flashover carbon tracks
        cv2.ellipse(flashover_img, (cx + 5, disc_y), (25, 10), 20, 0, 360, (20, 20, 25), -1)
        cv2.line(flashover_img, (cx - 15, disc_y - 15), (cx + 12, disc_y + 20), (15, 15, 20), 4)
    cv2.imwrite("static/uploads/inspections/sample_flashover_1.jpg", flashover_img)
    cv2.imwrite("static/sample_images/flashover_insulator.jpg", flashover_img)

    # 4. Corrosion / Rust
    corrosion_img = draw_pole_base()
    cx, cy = 400, 290
    cv2.line(corrosion_img, (cx, 210), (cx, cy + 160), (30, 50, 140), 8) # Rusted pin
    for i in range(5):
        disc_y = cy + (i * 32)
        cv2.ellipse(corrosion_img, (cx, disc_y), (48 - i * 2, 14), 0, 0, 360, (190, 200, 205), -1)
        # Rust staining streaks
        cv2.ellipse(corrosion_img, (cx, disc_y), (20, 8), 0, 0, 360, (35, 65, 160), -1)
    cv2.imwrite("static/uploads/inspections/sample_corrosion.jpg", corrosion_img)

    print("Sample inspection images successfully generated.")

if __name__ == "__main__":
    create_sample_images()
