"""
main.py
-------
Image Restoration in the Presence of Noise  --  Tkinter GUI

Workflow:
    1. Load an image (bundled sample or your own file)
    2. Choose a noise type and click "Add Noise"
    3. Choose a filter and click "Restore"
    4. Compare the Original / Noisy / Restored images and their PSNR
    5. Save the restored image, or export a full comparison table as CSV

Run with:  python main.py
"""

import csv
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import cv2
import matplotlib
matplotlib.use("TkAgg")  # backend that works inside Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import filters
import metrics
import noise

# ----------------------------------------------------------------------
# Dropdown contents
# ----------------------------------------------------------------------
NOISE_TYPES = ["Salt & Pepper", "Gaussian", "Speckle"]
FILTER_TYPES = ["Mean Filter", "Median Filter", "Gaussian Filter", "Histogram Equalization"]
KERNEL_SIZES = ["3", "5", "7", "9"]

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(HERE, "images")

# ----------------------------------------------------------------------
# Colour palette (soft, modern, low-contrast)
# ----------------------------------------------------------------------
BG = "#eef1f8"        # page background
CARD = "#ffffff"      # card / panel background
TEXT = "#1f2937"      # main text
MUTED = "#6b7280"     # secondary text
ACCENT = "#4f46e5"    # primary buttons
ACCENT_HOVER = "#4338ca"
BORDER = "#e2e6f0"    # thin card borders
TROUGH = "#dfe3ee"


def to_display(image):
    """Convert an OpenCV BGR image to something matplotlib can show."""
    if image is None:
        return None
    if image.ndim == 2:
        return image  # grayscale -> shown with a gray colormap
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


class RestorationApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Restoration in the Presence of Noise")
        root.geometry("1200x820")
        root.minsize(1000, 720)
        root.configure(bg=BG)

        # Images currently being worked on.
        self.original = None   # the clean image
        self.noisy = None      # the corrupted image
        self.restored = None   # the filtered result
        self._last_rows = None
        self.sample_map = {}

        self._setup_style()
        self._setup_fonts()
        self._build_header()
        self._build_controls()
        self._build_status()
        self._build_footer()
        self._build_figure()   # packed last so it fills only the leftover space
        self._load_sample_list()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Card.TLabel", background=CARD, foreground=TEXT)
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED)

        # Combobox
        style.configure("TCombobox", padding=4, borderwidth=1,
                        fieldbackground=CARD, background=CARD,
                        foreground=TEXT, arrowcolor=ACCENT,
                        bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD,
                        relief="flat")
        style.map("TCombobox",
                  fieldbackground=[("readonly", CARD)],
                  selectbackground=[("readonly", CARD)],
                  selectforeground=[("readonly", TEXT)],
                  bordercolor=[("focus", ACCENT)])

        # Scale (noise level)
        style.configure("TScale", background=CARD, troughcolor=TROUGH,
                        bordercolor=CARD, lightcolor=ACCENT, darkcolor=ACCENT)

        # Buttons
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                        borderwidth=0, focusthickness=0, padding=(16, 9),
                        relief="flat")
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
                  foreground=[("disabled", "#c7cbe0")])

        style.configure("Secondary.TButton", background=CARD, foreground=TEXT,
                        borderwidth=1, bordercolor=BORDER, focusthickness=0,
                        padding=(14, 8), relief="flat")
        style.map("Secondary.TButton",
                  background=[("active", "#f2f4fa"), ("pressed", "#e8ebf5")],
                  bordercolor=[("active", ACCENT)])

        style.configure("Ghost.TButton", background=CARD, foreground=MUTED,
                        borderwidth=0, focusthickness=0, padding=(10, 6),
                        relief="flat")
        style.map("Ghost.TButton",
                  background=[("active", "#f2f4fa")],
                  foreground=[("active", ACCENT)])

        # Popdown list colours
        self.root.option_add("*TCombobox*Listbox.background", CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.borderWidth", 0)

    def _setup_fonts(self):
        base = tkfont.nametofont("TkDefaultFont")
        family = base.cget("family")
        self.f_title = (family, 15, "bold")
        self.f_sub = (family, 9)
        self.f_head = (family, 9, "bold")
        self.f_label = (family, 10)
        self.f_chip = (family, 11, "bold")

    # ------------------------------------------------------------------
    # Small building blocks
    # ------------------------------------------------------------------
    def _card(self, parent, heading):
        """A white 'card' with a thin border and an optional heading."""
        outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                         highlightthickness=1)
        inner = tk.Frame(outer, bg=CARD, padx=16, pady=14)
        inner.pack(fill="both", expand=True)
        if heading:
            tk.Label(inner, text=heading, bg=CARD, fg=MUTED,
                     font=self.f_head).pack(anchor="w", pady=(0, 10))
        return outer, inner

    # ------------------------------------------------------------------
    # Layout sections
    # ------------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=CARD, highlightbackground=BORDER,
                          highlightthickness=0)
        header.pack(side=tk.TOP, fill=tk.X)

        left = tk.Frame(header, bg=CARD, padx=20, pady=14)
        left.pack(side=tk.LEFT)
        tk.Label(left, text="Image Restoration", bg=CARD, fg=TEXT,
                 font=self.f_title).pack(anchor="w")
        tk.Label(left, text="Noise removal with Mean, Median, Gaussian & Histogram Equalization",
                 bg=CARD, fg=MUTED, font=self.f_sub).pack(anchor="w")

        right = tk.Frame(header, bg=CARD, padx=20, pady=14)
        right.pack(side=tk.RIGHT)

        ttk.Label(right, text="Sample", style="Card.TLabel").grid(row=0, column=0, padx=(0, 6))
        self.sample_var = tk.StringVar()
        self.sample_combo = ttk.Combobox(right, textvariable=self.sample_var,
                                         width=16, state="readonly")
        self.sample_combo.grid(row=0, column=1, padx=(0, 10))
        self.sample_combo.bind("<<ComboboxSelected>>", self._on_sample_selected)

        ttk.Button(right, text="Open File...", style="Secondary.TButton",
                   command=self.load_image).grid(row=0, column=2)

        # thin divider under the header
        tk.Frame(self.root, bg=BORDER, height=1).pack(side=tk.TOP, fill=tk.X)

    def _build_controls(self):
        wrap = tk.Frame(self.root, bg=BG, padx=20, pady=16)
        wrap.pack(side=tk.TOP, fill=tk.X)
        wrap.columnconfigure(0, weight=1, uniform="cards")
        wrap.columnconfigure(1, weight=1, uniform="cards")

        # --- Card 1: noise ---
        noise_card, nc = self._card(wrap, "STEP 1  ·  ADD NOISE")
        noise_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        row = tk.Frame(nc, bg=CARD)
        row.pack(fill=tk.X)
        tk.Label(row, text="Noise type", bg=CARD, fg=TEXT, font=self.f_label).pack(side=tk.LEFT)
        self.noise_var = tk.StringVar(value=NOISE_TYPES[0])
        ttk.Combobox(row, textvariable=self.noise_var, values=NOISE_TYPES,
                     width=16, state="readonly").pack(side=tk.RIGHT)

        row = tk.Frame(nc, bg=CARD)
        row.pack(fill=tk.X, pady=(12, 0))
        tk.Label(row, text="Level", bg=CARD, fg=TEXT, font=self.f_label).pack(side=tk.LEFT)
        self.level_label = tk.Label(row, text="25", bg=CARD, fg=ACCENT, font=self.f_chip, width=3)
        self.level_label.pack(side=tk.RIGHT)
        self.level_var = tk.IntVar(value=25)
        ttk.Scale(nc, from_=1, to=50, variable=self.level_var,
                  orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 0))
        self.level_var.trace_add("write", self._update_level_label)

        ttk.Button(nc, text="Add Noise", style="Accent.TButton",
                   command=self.add_noise).pack(fill=tk.X, pady=(14, 0))

        # --- Card 2: restore ---
        filter_card, fc = self._card(wrap, "STEP 2  ·  RESTORE")
        filter_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        row = tk.Frame(fc, bg=CARD)
        row.pack(fill=tk.X)
        tk.Label(row, text="Filter", bg=CARD, fg=TEXT, font=self.f_label).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value=FILTER_TYPES[0])
        ttk.Combobox(row, textvariable=self.filter_var, values=FILTER_TYPES,
                     width=19, state="readonly").pack(side=tk.RIGHT)

        row = tk.Frame(fc, bg=CARD)
        row.pack(fill=tk.X, pady=(12, 0))
        tk.Label(row, text="Kernel size", bg=CARD, fg=TEXT, font=self.f_label).pack(side=tk.LEFT)
        self.kernel_var = tk.StringVar(value="5")
        ttk.Combobox(row, textvariable=self.kernel_var, values=KERNEL_SIZES,
                     width=4, state="readonly").pack(side=tk.RIGHT)

        ttk.Button(fc, text="Restore", style="Accent.TButton",
                   command=self.restore).pack(fill=tk.X, pady=(14, 0))

    def _build_figure(self):
        holder = tk.Frame(self.root, bg=BG, padx=20)
        holder.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(10, 5), dpi=100, facecolor=BG)
        self.axes = [self.figure.add_subplot(1, 3, i + 1) for i in range(3)]
        self.figure.subplots_adjust(left=0.02, right=0.98, top=0.90,
                                    bottom=0.02, wspace=0.06)

        self.canvas = FigureCanvasTkAgg(self.figure, master=holder)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=BG, highlightthickness=0)
        widget.pack(fill=tk.BOTH, expand=True)
        self._draw()

    def _build_status(self):
        bar = tk.Frame(self.root, bg=BG, padx=20, pady=4)
        bar.pack(side=tk.TOP, fill=tk.X)

        chips = tk.Frame(bar, bg=BG)
        chips.pack(side=tk.LEFT)

        self.noisy_chip = self._chip(chips, "Noisy", "amber")
        self.noisy_chip.pack(side=tk.LEFT)
        self.restored_chip = self._chip(chips, "Restored", "green")
        self.restored_chip.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(bar, text="Reset", style="Ghost.TButton",
                   command=self.reset).pack(side=tk.RIGHT)

    def _chip(self, parent, name, tone):
        colours = {"amber": ("#fef3c7", "#92400e"),
                   "green": ("#dcfce7", "#166534")}
        bg, fg = colours[tone]
        chip = tk.Frame(parent, bg=bg, padx=12, pady=6)
        tk.Label(chip, text=f"{name}", bg=bg, fg=fg,
                 font=self.f_sub).pack(side=tk.LEFT, padx=(0, 6))
        value = tk.Label(chip, text="-- dB", bg=bg, fg=fg, font=self.f_chip)
        value.pack(side=tk.LEFT)
        chip.value_label = value  # convenience handle
        return chip

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=BG, padx=20, pady=16)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(footer, text="Save Restored Image", style="Secondary.TButton",
                   command=self.save_restored).pack(side=tk.LEFT)
        self.compare_btn = ttk.Button(
            footer, text="Run Full Comparison", style="Accent.TButton",
            command=self.run_comparison)
        self.compare_btn.pack(side=tk.RIGHT)
        self.export_btn = ttk.Button(
            footer, text="Export CSV", style="Secondary.TButton",
            command=self.export_csv)
        self.export_btn.pack(side=tk.RIGHT, padx=(0, 10))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _update_level_label(self, *_):
        self.level_label.config(text=str(self.level_var.get()))

    def _draw(self):
        """Redraw the three image panels as clean framed cards."""
        for ax, img, title in zip(
                self.axes,
                [self.original, self.noisy, self.restored],
                ["Original", "Noisy", "Restored"]):
            ax.clear()
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor(CARD)
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(BORDER)
                spine.set_linewidth(1)
            ax.set_title(title, color=TEXT, fontsize=11, pad=8)

            disp = to_display(img)
            if disp is None:
                ax.text(0.5, 0.5, "No image yet", ha="center", va="center",
                        color=MUTED, fontsize=11, transform=ax.transAxes)
            else:
                cmap = "gray" if disp.ndim == 2 else None
                ax.imshow(disp, cmap=cmap)

        self.figure.patch.set_facecolor(BG)
        self.canvas.draw_idle()

    def _update_psnr(self, noisy_psnr=None, restored_psnr=None):
        self.noisy_chip.value_label.config(
            text="-- dB" if noisy_psnr is None else f"{noisy_psnr:.2f} dB")
        self.restored_chip.value_label.config(
            text="-- dB" if restored_psnr is None else f"{restored_psnr:.2f} dB")

    # ------------------------------------------------------------------
    # Sample handling
    # ------------------------------------------------------------------
    def _load_sample_list(self):
        if not os.path.isdir(IMAGES_DIR):
            return
        files = sorted(f for f in os.listdir(IMAGES_DIR)
                       if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")))
        self.sample_map = {os.path.splitext(f)[0]: os.path.join(IMAGES_DIR, f)
                           for f in files}
        if not self.sample_map:
            return
        names = list(self.sample_map.keys())
        self.sample_combo.configure(values=names)
        self.sample_var.set(names[0])
        self._open_path(self.sample_map[names[0]])  # show something immediately

    def _on_sample_selected(self, _event=None):
        path = self.sample_map.get(self.sample_var.get())
        if path:
            self._open_path(path)

    def _open_path(self, path):
        image = cv2.imread(path, cv2.IMREAD_COLOR)
        if image is None:
            messagebox.showerror("Error", "Could not read that image file.")
            return
        self.original = image
        self.noisy = None
        self.restored = None
        self._update_psnr()
        self._draw()

    # ------------------------------------------------------------------
    # Core operations (shared by the UI and the comparison table)
    # ------------------------------------------------------------------
    def _apply_noise(self, image, noise_type, level):
        if noise_type == "Salt & Pepper":
            return noise.add_salt_pepper(image, amount=level / 1000.0)
        if noise_type == "Gaussian":
            return noise.add_gaussian(image, mean=0, sigma=level)
        if noise_type == "Speckle":
            return noise.add_speckle(image, sigma=level / 100.0)
        raise ValueError(f"Unknown noise type: {noise_type}")

    def _apply_filter(self, image, filter_type, ksize):
        if filter_type == "Mean Filter":
            return filters.mean_filter(image, ksize=ksize)
        if filter_type == "Median Filter":
            return filters.median_filter(image, ksize=ksize)
        if filter_type == "Gaussian Filter":
            return filters.gaussian_filter(image, ksize=ksize)
        if filter_type == "Histogram Equalization":
            return filters.histogram_equalization(image)
        raise ValueError(f"Unknown filter type: {filter_type}")

    def _require_image(self):
        if self.original is None:
            messagebox.showwarning("No image", "Please load an image first.")
            return False
        return True

    # ------------------------------------------------------------------
    # Button actions
    # ------------------------------------------------------------------
    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                       ("All files", "*.*")])
        if path:
            self._open_path(path)

    def add_noise(self):
        if not self._require_image():
            return
        self.noisy = self._apply_noise(
            self.original, self.noise_var.get(), self.level_var.get())
        self.restored = None
        self._update_psnr(noisy_psnr=metrics.psnr(self.original, self.noisy))
        self._draw()

    def restore(self):
        if not self._require_image():
            return
        if self.noisy is None:
            messagebox.showinfo("No noisy image",
                                "Add noise first, then restore.")
            return
        ksize = int(self.kernel_var.get())
        self.restored = self._apply_filter(self.noisy, self.filter_var.get(), ksize)
        self._update_psnr(noisy_psnr=metrics.psnr(self.original, self.noisy),
                          restored_psnr=metrics.psnr(self.original, self.restored))
        self._draw()

    def reset(self):
        self.noisy = None
        self.restored = None
        self._update_psnr()
        self._draw()

    def save_restored(self):
        if self.restored is None:
            messagebox.showwarning("Nothing to save", "Restore an image first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save restored image", defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if not path:
            return
        cv2.imwrite(path, self.restored)
        messagebox.showinfo("Saved", f"Restored image saved to:\n{path}")

    # ------------------------------------------------------------------
    # Full comparison table
    # ------------------------------------------------------------------
    def run_comparison(self):
        if not self._require_image():
            return
        level = self.level_var.get()
        ksize = int(self.kernel_var.get())

        rows = []
        for noise_type in NOISE_TYPES:
            noisy = self._apply_noise(self.original, noise_type, level)
            row = {"noise": noise_type, "noisy_psnr": metrics.psnr(self.original, noisy)}
            for filter_type in FILTER_TYPES:
                restored = self._apply_filter(noisy, filter_type, ksize)
                row[filter_type] = metrics.psnr(self.original, restored)
            rows.append(row)

        self._last_rows = rows
        self._last_meta = (level, ksize)
        self._show_table(rows, level, ksize)

    def _show_table(self, rows, level, ksize):
        win = tk.Toplevel(self.root)
        win.title("PSNR Comparison (dB)")
        win.configure(bg=BG)
        win.geometry("760x360")

        tk.Label(win, text="PSNR Comparison", bg=BG, fg=TEXT,
                 font=self.f_title).pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(win, text=f"Noise level = {level}   ·   kernel size = {ksize}   ·   higher is better",
                 bg=BG, fg=MUTED, font=self.f_sub).pack(anchor="w", padx=20, pady=(0, 10))

        cols = ("noise", "noisy") + tuple(FILTER_TYPES)
        tree = ttk.Treeview(win, columns=cols, show="headings", height=4)
        headings = ["Noise", "Noisy"] + [f.replace(" Filter", "").replace(" Equalization", " EQ")
                                         for f in FILTER_TYPES]
        for col, head in zip(cols, headings):
            tree.heading(col, text=head)
            tree.column(col, anchor="center", width=110)
        tree.column("noise", anchor="w", width=120)

        for row in rows:
            values = [row["noise"], f"{row['noisy_psnr']:.2f}"] + \
                     [f"{row[f]:.2f}" for f in FILTER_TYPES]
            tree.insert("", "end", values=values)
        tree.pack(fill=tk.X, padx=20)

        tk.Label(win, text="Rule of thumb: Median is usually best for Salt & Pepper; "
                           "Mean / Gaussian are best for Gaussian noise. "
                           "Histogram Equalization improves contrast, not noise.",
                 bg=BG, fg=MUTED, font=self.f_sub, wraplength=700,
                 justify="left").pack(anchor="w", padx=20, pady=(12, 0))

        ttk.Button(win, text="Export CSV", style="Accent.TButton",
                   command=self.export_csv).pack(pady=16)

    def export_csv(self):
        if not self._last_rows:
            messagebox.showinfo("No data", "Run the full comparison first.")
            return
        path = filedialog.asksaveasfilename(
            title="Export PSNR results", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Noise Type", "Noisy PSNR"] + FILTER_TYPES)
            for row in self._last_rows:
                writer.writerow([row["noise"], f"{row['noisy_psnr']:.2f}"]
                                + [f"{row[f]:.2f}" for f in FILTER_TYPES])
        messagebox.showinfo("Exported", f"Results saved to:\n{path}")


def main():
    root = tk.Tk()
    RestorationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
