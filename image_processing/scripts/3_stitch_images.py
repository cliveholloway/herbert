import cv2
import numpy as np
import sys

def load_grayscale(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    return img

def find_best_overlap_cut(img1, img2, max_overlap=10):
    bottom_part = img1[-max_overlap:]
    top_part = img2[:max_overlap]

    best_score = float('inf')
    best_row = (0, 0)

    for i in range(max_overlap):
        for j in range(max_overlap):
            row1 = bottom_part[i]
            row2 = top_part[j]
            if row1.shape != row2.shape:
                continue
            diff = np.sum(np.abs(row1.astype(np.int16) - row2.astype(np.int16)))
            if diff < best_score:
                best_score = diff
                best_row = (i, j)

    print(f"Best row match: img1[-{max_overlap}+{best_row[0]}], img2[{best_row[1]}]")
    return best_row

def stitch_images(img1, img2, max_overlap=10):
    i_cut, j_cut = find_best_overlap_cut(img1, img2, max_overlap)
    cut1 = img1.shape[0] - max_overlap + i_cut
    cut2 = j_cut
    return np.vstack([img1[:cut1], img2[cut2:]])

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python stitch_overlap.py image1.png image2.png output.png")
        sys.exit(1)

    img1 = load_grayscale(sys.argv[1])
    img2 = load_grayscale(sys.argv[2])

    if img1.shape[1] != img2.shape[1]:
        print("ERROR: Image widths do not match. Please crop or deskew before stitching.")
        sys.exit(1)

    result = stitch_images(img1, img2, max_overlap=10)
    result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(sys.argv[3], result_bgr)
    print(f"Stitched image saved to: {sys.argv[3]}")

