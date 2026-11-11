from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def sample(array, height=700, width=900):
    return array[
        :: max(1, (array.shape[0] + height - 1) // height),
        :: max(1, (array.shape[1] + width - 1) // width),
    ]


def images(name, reference, distorted, row):
    if name == "Reconstruction":
        return reference[row], distorted[row]
    return reference[:, row, :], distorted[:, row, :]


def scales(reference, error):
    low, high = np.percentile(sample(reference), [1, 99])
    limit = max(float(np.percentile(np.abs(sample(error)), 99.5)), 1e-12)
    return float(low), float(high), limit


def stage_plot(name, reference, distorted, stats, path, row):
    a, b = images(name, reference, distorted, row)
    a, b = a.astype(np.float32, copy=False), b.astype(np.float32, copy=False)
    error = b - a
    low, high, limit = scales(a, error)
    figure, axes = plt.subplots(2, 3, figsize=(15, 9), layout="constrained")
    extent = (0, a.shape[1], a.shape[0], 0)
    views = [
        (axes[0, 0], a, "Reference (1–99% display)", "gray", low, high),
        (axes[0, 1], b, "Kakadu MCT (same scale)", "gray", low, high),
        (axes[0, 2], error, "Signed error (99.5% display)", "RdBu_r", -limit, limit),
        (
            axes[1, 0],
            np.abs(error),
            "Absolute error (99.5% display)",
            "magma",
            0,
            limit,
        ),
    ]
    for axis, values, title, colormap, minimum, maximum in views:
        artist = axis.imshow(
            sample(values),
            cmap=colormap,
            vmin=minimum,
            vmax=maximum,
            aspect="auto",
            interpolation="nearest",
            extent=extent,
        )
        axis.set_title(title)
        axis.set_xlabel("Detector column" if name != "Reconstruction" else "X pixel")
        axis.set_ylabel("Projection index" if name != "Reconstruction" else "Y pixel")
        figure.colorbar(artist, ax=axis, shrink=0.8)
    index = a.shape[0] // 2
    axes[1, 1].plot(a[index], label="Reference", linewidth=1)
    axes[1, 1].plot(b[index], label="Kakadu MCT", linewidth=1, alpha=0.75)
    axes[1, 1].set_title(f"Horizontal profile at row {index}")
    axes[1, 1].set_xlabel("Detector column" if name != "Reconstruction" else "X pixel")
    axes[1, 1].legend()
    histogram = sample(error).ravel()
    if name == "Reconstruction":
        histogram = histogram[histogram != 0]
    axes[1, 2].hist(histogram, bins=70, range=(-limit, limit))
    axes[1, 2].set_title(
        "Error distribution (nonzero, sampled)"
        if name == "Reconstruction"
        else "Error distribution (sampled)"
    )
    axes[1, 2].set_xlabel("Compressed − reference")
    axes[1, 2].set_ylabel("Pixels")
    figure.suptitle(
        f"{name} | RMSE {stats['rmse']:.4g} | NRMSE {stats['nrmse']:.3%} | PSNR {stats['psnr']:.2f} dB"
    )
    figure.savefig(path, dpi=115)
    plt.close(figure)


def overview(stages, stats, path, ratio, backend, row):
    figure, axes = plt.subplots(len(stages), 3, figsize=(13, 12), layout="constrained")
    for i, (name, reference, distorted) in enumerate(stages):
        a, b = images(name, reference, distorted, row)
        error = b.astype(np.float32) - a.astype(np.float32)
        low, high, limit = scales(a, error)
        for axis, data, colormap, minimum, maximum in zip(
            axes[i],
            (a, b, np.abs(error)),
            ("gray", "gray", "magma"),
            (low, low, 0),
            (high, high, limit),
        ):
            axis.imshow(
                sample(data),
                cmap=colormap,
                vmin=minimum,
                vmax=maximum,
                aspect="auto",
                interpolation="nearest",
            )
            axis.set_xticks([])
            axis.set_yticks([])
        axes[i, 0].set_ylabel(
            f"{name}\nRMSE {stats[i]['rmse']:.4g}\nNRMSE {stats[i]['nrmse']:.3%}"
        )
    for axis, title in zip(axes[0], ("Reference", "Kakadu MCT", "Absolute error")):
        axis.set_title(title)
    figure.suptitle(
        f"Kakadu MCT {ratio:.2f}× | {backend} reconstruction | detector row {row}"
    )
    figure.savefig(path, dpi=115)
    plt.close(figure)


def plot(stages, stats, output, ratio, backend, row):
    output = Path(output)
    plots = output / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    for index, ((name, reference, distorted), values) in enumerate(
        zip(stages, stats), 1
    ):
        path = plots / f"{index:02d}_{name.lower()}.png"
        stage_plot(name, reference, distorted, values, path, row)
        print(f"Plot: {path}", flush=True)
    overview(stages, stats, output / "pipeline.png", ratio, backend, row)
