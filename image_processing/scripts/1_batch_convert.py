import os
from pathlib import Path
from PIL import Image

def convert_tif_to_png(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for tif_path in input_dir.glob("*.tif*"):
        with Image.open(tif_path) as img:
            png_path = output_dir / (tif_path.stem + ".png")
            img.save(png_path, format="PNG")
            print(f"Converted {tif_path} to {png_path}")

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python batch_convert.py input_dir output_dir")
        sys.exit(1)
    convert_tif_to_png(sys.argv[1], sys.argv[2])
