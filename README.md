# Image Restoration in the Presence of Noise

A simple desktop application (Python + Tkinter) that:
1. loads an image,
2. adds **Salt & Pepper**, **Gaussian**, or **Speckle** noise,
3. restores it with a **Mean**, **Median**, **Gaussian** filter or **Histogram Equalization**,
4. and compares the results using **PSNR**.

This is a starter-level image-processing project — only classic, well-known
techniques are used.

## Requirements

- Python 3
- Packages in `requirements.txt`

## Install

```bash
pip install -r requirements.txt
```

Tkinter needs the system Tk library. If `import tkinter` fails with
`libtk8.6.so` missing, install it:

| Distro        | Command                     |
|---------------|-----------------------------|
| Arch/CachyOS  | `sudo pacman -S tk`         |
| Debian/Ubuntu | `sudo apt install python3-tk` |

## Run

```bash
python main.py
```

The app opens with a sample image already loaded, so you can start immediately.

## Sample images

The `images/` folder ships with ready-to-use test images:

| File             | Why it's useful                                  |
|------------------|--------------------------------------------------|
| `lena.jpg`       | Classic portrait — smooth areas + fine detail    |
| `baboon.jpg`     | Heavily textured — a hard case for any filter    |
| `fruits.jpg`     | Colourful natural scene                          |
| `board.jpg`      | Fine high-frequency detail                       |
| `sudoku.png`     | Sharp text/lines — noise is very visible         |
| `lowcontrast.png`| Faded image — shows off Histogram Equalization   |

`lena/baboon/fruits/board/sudoku` come from OpenCV's public sample data.
To re-download / regenerate them:

```bash
python setup_samples.py
```

## How to use

1. Pick a **Sample** from the top-right, or click **Open File...** for your own image.
2. In **Step 1**, choose a **Noise type** and drag the **Level** slider, then click **Add Noise**.
3. In **Step 2**, choose a **Filter** and a **Kernel size**, then click **Restore**.
4. The window shows **Original | Noisy | Restored** with the PSNR of each.
5. **Save Restored Image** writes the result to a file.
6. **Run Full Comparison** tests every noise type against every filter and
   shows a PSNR table; **Export CSV** saves it for your report.

## Files

| File                 | Purpose                                          |
|----------------------|--------------------------------------------------|
| `main.py`            | Tkinter GUI + application logic                  |
| `noise.py`           | Salt & Pepper / Gaussian / Speckle noise         |
| `filters.py`         | Mean / Median / Gaussian filters + Histogram EQ  |
| `metrics.py`         | PSNR calculation                                 |
| `setup_samples.py`   | Downloads / generates the sample images          |

## Expected results (for your report)

- **Salt & Pepper** noise → **Median** filter works best.
- **Gaussian** noise → **Mean** or **Gaussian** filter works best.
- **Histogram Equalization** improves *contrast* but does **not** remove noise,
  so its PSNR is usually low — a good point to discuss.

Higher PSNR (in dB) means the restored image is closer to the original.
