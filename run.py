import argparse
import csv
from pathlib import Path

import tifffile

from absorbance import absorbance
from codec import roundtrip
from load import load
from metrics import compare
from normalize import fields, normalize
from plot import plot
from reconstruct import reconstruct


root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--data", type=Path, default=root / "data")
parser.add_argument("--bin", type=Path, default=root / "bin")
parser.add_argument("--out", type=Path, default=root / "results")
parser.add_argument("--ratio", type=float, default=4)
parser.add_argument("--center", type=float)
parser.add_argument("--size", type=int, default=512)
parser.add_argument("--row", type=int, default=2)
parser.add_argument("--preview-angles", type=int, default=500)
parser.add_argument("--preview-detectors", type=int, default=512)
parser.add_argument("--backend", choices=["auto", "tomopy", "skimage"], default="auto")
parser.add_argument("--cutoff", type=float)
args = parser.parse_args()

projections = load(args.data, "tomography")
flats = load(args.data, "flatfield")
darks = load(args.data, "darkfield")
if args.ratio <= 1 or args.size <= 0 or args.size > projections.shape[2]:
    parser.error("ratio must exceed 1 and size must be within detector width")
if not 0 <= args.row < projections.shape[1]:
    parser.error("row must be within detector height")
center = args.center if args.center is not None else projections.shape[2] / 2
args.out.mkdir(parents=True, exist_ok=True)

print(
    f"Loaded {projections.shape[0]} projections and {len(flats)}/{len(darks)} flat/dark fields",
    flush=True,
)
decoded, actual_ratio = roundtrip(projections, args.out, args.ratio, args.bin)
print(f"Kakadu MCT: {actual_ratio:.2f}x", flush=True)
flat, dark = fields(flats, darks)
reference_norm = normalize(projections, flat, dark, args.cutoff)
decoded_norm = normalize(decoded, flat, dark, args.cutoff)
reference_abs = absorbance(reference_norm)
decoded_abs = absorbance(decoded_norm)
print(f"Reconstructing with {args.backend} ...", flush=True)
reference_volume, backend = reconstruct(
    reference_abs,
    center,
    args.size,
    args.backend,
    args.preview_angles,
    args.preview_detectors,
)
decoded_volume, _ = reconstruct(
    decoded_abs, center, args.size, backend, args.preview_angles, args.preview_detectors
)

stages = [
    ("Projection", projections, decoded),
    ("Normalization", reference_norm, decoded_norm),
    ("Absorbance", reference_abs, decoded_abs),
    ("Reconstruction", reference_volume, decoded_volume),
]
stats = [compare(a, b) for _, a, b in stages]
with (args.out / "metrics.csv").open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["stage", "rmse", "mae", "nrmse_p1_p99", "psnr_p1_p99"])
    writer.writerows(
        (name, *values.values()) for (name, _, _), values in zip(stages, stats)
    )

plot(stages, args.out, args.row)
tifffile.imwrite(args.out / "reference_reconstruction.tiff", reference_volume)
tifffile.imwrite(args.out / "compressed_reconstruction.tiff", decoded_volume)
for (name, _, _), values in zip(stages, stats):
    print(f"{name:15s} RMSE={values['rmse']:.6g} NRMSE={values['nrmse']:.3%}")
print(f"Output: {args.out}")
