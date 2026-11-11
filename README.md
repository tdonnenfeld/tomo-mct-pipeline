# MCT tomography distortion

Minimal modular reproduction of the absorbance-only processing chain using the four detector rows from the supplied scan.

```bash
pip install -r requirements.txt
python run.py --ratio 4
```

Files have a single role: `load.py` reads data, `codec.py` runs Kakadu, `normalize.py` corrects flat/dark fields, `absorbance.py` computes minus-log, `reconstruct.py` reconstructs, `metrics.py` compares, `plot.py` visualizes, `run.py` orchestrates.

The archive includes 2,000 4×2048 angular projections, 200 flats, 200 darks and the supplied Kakadu Linux 8.4 binaries. Kakadu's JPEG 2000 Part-2 reversible 5/3 multi-component transform operates across four neighboring angular projections; wavelet truncation makes the encoding lossy. The actual compression ratio is measured against the full uncompressed projection data.

The data archive does not include acquisition angles or the rotation center. Defaults: 2,000 uniformly spaced angles from 0° to just below 180°, fixed center at pixel 1024, four detector rows, float32 processing, mean flat/dark field, 1e-6 log floor, no normalization cutoff, ramp FBP, 512×512 central reconstruction crop. For fast `scikit-image` previews, the reconstruction uses 500 evenly selected projection angles and averages neighboring detector samples down to 512 columns. The projection, normalization and absorbance metrics still use all 2,000 angles and full detector width.

With TomoPy installed, `--backend auto` uses Gridrec; without it, `scikit-image` filtered backprojection is used instead. These are **not equivalent algorithms**. The `scikit-image` backend is for runnable previews, not exact ENDOR/Gridrec matching. The chosen backend is printed and appears in the figure. The float32 inverse-log floor prevents invalid logarithms and may differ from your ENDOR configuration. No center-of-rotation estimation is performed: both reconstruction branches use the same fixed center.

```bash
python run.py --ratio 8 --center 1023.5 --size 1024 --preview-detectors 1024 --preview-angles 1000 --backend skimage
python run.py --ratio 4 --center 1023.5 --size 2048 --backend tomopy
```

Outputs in `results/`: `compressed.j2c`, `pipeline.png`, `metrics.csv`, `reference_reconstruction.tiff`, and `compressed_reconstruction.tiff`. The `results/plots/` directory contains one detailed figure per stage: `01_projection.png`, `02_normalization.png`, `03_absorbance.png`, and `04_reconstruction.png`. Each figure shows reference, decoded, signed error, absolute error, a horizontal intensity profile, and an error histogram (nonzero errors only for reconstruction). The first three plot rows are sinograms (angles × detector position); the final row is a reconstructed cross-section. RMSE and MAE are computed on the complete stage arrays, while NRMSE/PSNR use the **same 1st–99th percentile range of that stage's reference**, not the raw 16-bit peak. Metrics are comparable between branches within a stage, not directly interchangeable between different physical representations.

TomoPy normalization reference: <https://tomopy.readthedocs.io/en/stable/_modules/tomopy/prep/normalize.html>

Reference and decoded images within a stage share a grayscale window from the sampled reference 1st–99th percentiles. Error maps use a symmetric signed scale or a nonnegative absolute scale up to the sampled error 99.5th percentile; this clips only the display, never the measurements. Plots are decimated for speed, but RMSE/MAE/NRMSE/PSNR in `metrics.csv` are computed from full stage arrays. The projection-space plots are sinograms for one detector row, while the reconstruction plot is a tomographic slice.
