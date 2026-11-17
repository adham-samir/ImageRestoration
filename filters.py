"""
filters.py
----------
Restoration / enhancement filters.

Each function is a thin wrapper around a standard OpenCV call, so the
code stays short and easy to explain. All filters accept both grayscale
and colour (BGR) images.

Included:
    - Mean filter
    - Median filter
    - Gaussian filter
    - Histogram Equalization
"""

import cv2


def mean_filter(image, ksize=5):
    """
    Mean (averaging) filter.

    Replaces each pixel with the average of its ksize x ksize
    neighbourhood. Good for Gaussian noise, but blurs edges.

    ksize must be a positive odd number, e.g. 3, 5, 7.
    """
    return cv2.blur(image, (ksize, ksize))


def median_filter(image, ksize=5):
    """
    Median filter.

    Replaces each pixel with the median of its ksize x ksize
    neighbourhood. Excellent for Salt & Pepper noise because it
    ignores extreme (black/white) pixels.

    ksize must be an odd number, e.g. 3, 5, 7.
    """
    return cv2.medianBlur(image, ksize)


def gaussian_filter(image, ksize=5, sigma=0):
    """
    Gaussian filter.

    Like the mean filter but gives more weight to nearby pixels,
    so it preserves edges slightly better.

    sigma = 0 lets OpenCV calculate it automatically from ksize.
    """
    return cv2.GaussianBlur(image, (ksize, ksize), sigma)


def histogram_equalization(image):
    """
    Histogram Equalization.

    Spreads out the pixel intensities so the image uses the full
    0-255 range, improving CONTRAST. Note: it is an enhancement
    technique - it does NOT remove noise, so we use it for comparison.

    - Grayscale : equalize directly.
    - Colour    : convert to YCrCb and equalize ONLY the Y (brightness)
                  channel, then convert back. This avoids colour shifts.
    """
    if image.ndim == 2:
        # Grayscale image.
        return cv2.equalizeHist(image)

    # Colour image: work in YCrCb colour space.
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y_equalized = cv2.equalizeHist(y)
    merged = cv2.merge((y_equalized, cr, cb))
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)
