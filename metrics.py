"""
metrics.py
----------
Image quality metrics.

For this project we only need PSNR (Peak Signal-to-Noise Ratio).
PSNR compares an original image against another image (noisy or restored)
and tells us, in decibels (dB), how close the two are.

The rule of thumb:
    - Higher PSNR  -> the images are MORE similar (better restoration)
    - Lower PSNR   -> the images are LESS similar (more distortion)

PSNR = 10 * log10( MAX^2 / MSE )
    where MAX = 255 (max pixel value for 8-bit images)
          MSE = mean squared error between the two images
"""

import numpy as np


def mse(original, other):
    """Mean Squared Error between two images (any number of channels)."""
    original = original.astype(np.float64)
    other = other.astype(np.float64)
    return np.mean((original - other) ** 2)


def psnr(original, other):
    """
    Peak Signal-to-Noise Ratio in decibels (dB).

    Parameters
    ----------
    original : np.ndarray  the clean reference image
    other    : np.ndarray  the image to compare (noisy or restored)

    Returns
    -------
    float : PSNR value in dB. Returns float('inf') for identical images.
    """
    error = mse(original, other)

    # If the images are identical there is no error -> infinite PSNR.
    if error == 0:
        return float("inf")

    max_pixel = 255.0
    return 10.0 * np.log10((max_pixel ** 2) / error)
