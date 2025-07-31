import cv2
import numpy as np
from PIL import Image
import os

def deskew_using_hough_lines(img_path, output_path, angle_threshold=0.25):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Probabilistic Hough Transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 720,  # 0.25 degree steps
        threshold=100,
        minLineLength=100,
        maxLineGap=10
    )

    if lines is None:
        print(f"{os.path.basename(img_path)}: No lines detected.")
        return

    angles = []
    for x1, y1, x2, y2 in lines[:, 0]:
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            continue
        angle = np.degrees(np.arctan2(dy, dx))
        if -10 < angle < 10:  # filter near-horizontal lines
            angles.append(angle)

    if not angles:
        print(f"{os.path.basename(img_path)}: No horizontal lines found.")
        return

    median_angle = np.median(angles)

    if abs(median_angle) < angle_threshold:
        print(f"{os.path.basename(img_path)}: Angle {median_angle:.2f}° < threshold. Skipped.")
        Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(output_path)
        return

    # Rotate the original image
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    Image.fromarray(cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)).save(output_path)
    print(f"{os.path.basename(img_path)}: Deskewed by {median_angle:.2f}°, saved.")

def batch_deskew(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for fname in sorted(os.listdir(input_dir)):
        if fname.lower().endswith((".tif", ".tiff", ".png", ".jpg", ".jpeg")):
            in_path = os.path.join(input_dir, fname)
            out_path = os.path.join(output_dir, os.path.splitext(fname)[0] + ".png")
            deskew_using_hough_lines(in_path, out_path)

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 deskew_hough_batch.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    batch_deskew(input_dir, output_dir)


