# AGENTS.md

## Purpose

Study how Kakadu JPEG 2000 Part-2 multi-component compression changes synchrotron tomography data across projection, flat/dark normalization, absorbance, and reconstruction stages.

## Design rules

- Keep the project small and readable. One Python file, one responsibility.
- Prefer straightforward functions and explicit data flow over frameworks or classes.
- Do not add inline code comments. Use clear names and update this file or `README.md` when behavior needs explanation.
- Do not add dependencies unless necessary.
- Keep reference and compressed branches identical after decoding, including reconstruction settings and rotation center.
- Preserve full-resolution metrics for the available projection-space stages.
- Never silently switch between a preview reconstruction and a full reconstruction.

## Files

- `run.py`: CLI arguments and pipeline orchestration.
- `load.py`: load projection, flat-field and dark-field TIFFs from a ZIP or directory.
- `codec.py`: Kakadu MCT encode/decode round trip and actual compression ratio.
- `normalize.py`: compute mean fields and flat/dark normalization.
- `absorbance.py`: negative logarithm of normalized transmission.
- `reconstruct.py`: TomoPy Gridrec or scikit-image filtered-backprojection preview.
- `metrics.py`: RMSE, MAE, reference-range NRMSE and PSNR.
- `plot.py`: one per-stage comparison figure, plus the overview figure. Plot full-resolution arrays without decimation; rendering to PNG may still scale images to the saved figure dimensions.

## Inputs and tools

- `data/SUBSAMPLED.zip` holds 2,000 uint16 projections, 200 flat-fields and 200 dark-fields, each 4 × 2048 pixels.
- `bin/kdu_compress`, `bin/kdu_expand` and `bin/libkdu_v84R.so` are the supplied Linux Kakadu 8.4 tools.
- The codec groups four consecutive angular projections as MCT components. Keep component order intact after decoding.
- The input archive has no trusted angles or rotation-center metadata. The current defaults are uniform angles over [0, π) and center at half the detector width. Do not present them as measured acquisition parameters.

## Run

```bash
python -m pip install -r requirements.txt
python run.py --ratio 4
```

For a fast explicit preview:

```bash
python run.py --ratio 4 --backend skimage --preview-angles 500 --preview-detectors 512
```

For Gridrec, install TomoPy in a compatible environment and use `--backend tomopy`.

## Scientific constraints

- TomoPy Gridrec and scikit-image filtered backprojection are not equivalent. Label the backend in figures and reports.
- The scikit-image preview subsamples angles and bins detector columns; projection-space statistics still use the full data.
- Use the same stage-specific reference range for normalization of a metric pair. Do not compare raw RMSE or PSNR across stages as though their units or peak values were identical.
- `absorbance.py` floors values before taking the logarithm. Any comparison with ENDOR should confirm the corresponding ENDOR setting.
- The fixed rotation center is shared by both branches to isolate compression effects. Center estimation is not reproduced.
- Do not treat these four detector rows as a complete 3D acquisition.

## Outputs and checks

- Write outputs under `results/`: `compressed.j2c`, `metrics.csv`, `results.md`, `pipeline.png`, `plots/01_projection.png`, `plots/02_normalization.png`, `plots/03_absorbance.png`, `plots/04_reconstruction.png`, and the reconstructed TIFFs.
- `results/results.md` reports the run summary and the `metrics.csv` table in plain-language terms, and embeds the per-stage figures plus the overview.
- After changing codec logic, verify decoded shape, dtype, angular ordering and the reported actual compression ratio.
- After changing preprocessing or reconstruction, verify both branches use the same parameters and that output arrays have matching shapes and finite-value behavior.
- Do not edit the input TIFF archive or Kakadu binaries.
- Keep generated images and large intermediate files out of source-code changes unless explicitly requested.

## Plot conventions

- The first three stages display a single-row sinogram (angle index × detector column); reconstruction displays one slice.
- Keep the reference and distorted image intensity scales identical within a stage.
- Only plot Reference, Kakadu MCT, and Absolute Error; use a sequential colormap for absolute errors.
- Use short titles and do not confuse clipped display values with full-array metrics.
- Stage PNGs use high-resolution rendering; the pipeline overview is a smaller summary.\n- Avoid saving large intermediate arrays only to produce plots.
