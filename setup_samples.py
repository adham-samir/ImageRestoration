"""
setup_samples.py
----------------
Populates the images/ folder with ready-to-use sample images.

It does two things:
  1. Downloads a few classic test images from OpenCV's public sample data
     (handy for image-processing assignments).
  2. Generates one extra synthetic low-contrast image so the effect of
     Histogram Equalization is easy to see.

Run:  python setup_samples.py
"""

import os
import urllib.request

import cv2
import numpy as np

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
BASE_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data"

# Classic test images shipped with OpenCV.
SAMPLES = ["lena.jpg", "baboon.jpg", "fruits.jpg", "board.jpg", "sudoku.png"]


def download_samples():
    os.makedirs(IMG_DIR, exist_ok=True)
    for name in SAMPLES:
        dest = os.path.join(IMG_DIR, name)
        if os.path.exists(dest):
            print(f"  already have {name}")
            continue
        url = f"{BASE_URL}/{name}"
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  downloaded  {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED      {name} ({exc})")


def make_low_contrast():
    """Create a dull, washed-out image with a very narrow brightness range."""
    dest = os.path.join(IMG_DIR, "lowcontrast.png")
    if os.path.exists(dest):
        print("  already have lowcontrast.png")
        return

    h, w = 400, 400
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Narrow vertical gradient (only ~100..150 brightness, so it looks flat).
    for y in range(h):
        v = int(100 + 50 * y / h)
        img[y, :] = (v, v - 8, v - 16)

    cv2.rectangle(img, (40, 40), (180, 180), (128, 120, 112), -1)
    cv2.circle(img, (285, 110), 70, (142, 134, 126), -1)
    cv2.rectangle(img, (220, 240), (360, 360), (118, 110, 102), -1)
    cv2.line(img, (40, 360), (200, 240), (110, 104, 98), 4)

    cv2.imwrite(dest, img)
    print("  generated   lowcontrast.png")


def main():
    print("Setting up sample images in:", IMG_DIR)
    download_samples()
    make_low_contrast()
    print("Done.")


if __name__ == "__main__":
    main()
