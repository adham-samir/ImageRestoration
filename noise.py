"""
noise.py
--------
Functions that CORRUPT a clean image by adding noise.
We need these so the project has a "noisy version" to restore from.

Three common noise types for a starter image-processing course:

    1. Salt & Pepper noise  -> random black and white dots
    2. Gaussian noise       -> random value added to every pixel
    3. Speckle noise        -> multiplicative noise (image * random)

All functions take a colour (BGR) or grayscale image and return a new
image of the same shape and dtype (uint8).
"""

import numpy as np


def add_salt_pepper(image, amount=0.02):
    """
    Add Salt & Pepper noise.

    'Salt' = white (255) pixels.
    'Pepper' = black (0) pixels.

    Parameters
    ----------
    image  : np.ndarray  input image (grayscale or colour)
    amount : float       fraction of pixels to corrupt (0.02 = 2%)

    Returns
    -------
    np.ndarray : noisy image
    """
    noisy = image.copy()
    h, w = noisy.shape[:2]

    # How many pixels to turn into salt or pepper in total.
    num_pixels = int(amount * h * w)
    num_salt = num_pixels // 2
    num_pepper = num_pixels - num_salt

    # Salt -> white pixels
    ys = np.random.randint(0, h, num_salt)
    xs = np.random.randint(0, w, num_salt)
    noisy[ys, xs] = 255

    # Pepper -> black pixels
    ys = np.random.randint(0, h, num_pepper)
    xs = np.random.randint(0, w, num_pepper)
    noisy[ys, xs] = 0

    return noisy


def add_gaussian(image, mean=0, sigma=25):
    """
    Add additive Gaussian (normal) noise.

    A random value drawn from N(mean, sigma) is added to every pixel.
    This is the most common noise model in image processing.

    Parameters
    ----------
    image : np.ndarray  input image
    mean  : float       average of the noise
    sigma : float       standard deviation (strength) of the noise

    Returns
    -------
    np.ndarray : noisy image
    """
    image = image.astype(np.float64)

    # Draw random noise of the same shape as the image.
    noise = np.random.normal(mean, sigma, image.shape)

    noisy = image + noise

    # Keep values valid and return as uint8.
    return np.clip(noisy, 0, 255).astype(np.uint8)


def add_speckle(image, sigma=0.2):
    """
    Add multiplicative speckle noise.

    Noisy pixel = pixel + pixel * random_noise
    Speckle is common in radar / ultrasound / laser images.

    Parameters
    ----------
    image : np.ndarray  input image
    sigma : float       strength of the noise

    Returns
    -------
    np.ndarray : noisy image
    """
    image = image.astype(np.float64)

    noise = np.random.normal(0, sigma, image.shape)
    noisy = image + image * noise

    return np.clip(noisy, 0, 255).astype(np.uint8)
