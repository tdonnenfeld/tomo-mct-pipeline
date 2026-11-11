from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


TITLES = ("Reference", "Kakadu MCT", "Absolute Error")


def images(name, reference, compressed, row):
    if name == "Reconstruction":
        return reference[row], compressed[row]
    return reference[:, row, :], compressed[:, row, :]


def panels(axes, reference, compressed, titles=False):
    error = np.abs(compressed.astype(np.float32) - reference.astype(np.float32))
    low, high = np.percentile(reference, [1, 99])
    limit = max(float(np.percentile(error, 99.5)), 1e-12)
    for axis, image, title, cmap, vmin, vmax in zip(
        axes,
        (reference, compressed, error),
        TITLES,
        ("gray", "gray", "magma"),
        (low, low, 0),
        (high, high, limit),
    ):
        artist = axis.imshow(
            image, cmap=cmap, vmin=vmin, vmax=vmax,
            aspect="auto", interpolation="none"
        )
        axis.set_xticks([])
        axis.set_yticks([])
        if titles:
            axis.set_title(title)
        axis.figure.colorbar(artist, ax=axis, fraction=0.045, pad=0.02)


def stage_plot(name, reference, compressed, path, row):
    reference, compressed = images(name, reference, compressed, row)
    figure, axes = plt.subplots(1, 3, figsize=(32, 11), layout="constrained")
    panels(axes, reference, compressed, titles=True)
    figure.suptitle(name)
    figure.savefig(path, dpi=220)
    plt.close(figure)


def overview(stages, path, row):
    figure, axes = plt.subplots(len(stages), 3, figsize=(13, 12), layout="constrained")
    axes = np.atleast_2d(axes)
    for index, (name, reference, compressed) in enumerate(stages):
        reference, compressed = images(name, reference, compressed, row)
        panels(axes[index], reference, compressed, titles=index == 0)
        axes[index, 0].set_ylabel(name)
    figure.savefig(path, dpi=115)
    plt.close(figure)


def plot(stages, output, row):
    output = Path(output)
    plots = output / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    for index, (name, reference, compressed) in enumerate(stages, 1):
        stage_plot(name, reference, compressed, plots / f"{index:02d}_{name.lower()}.png", row)
    overview(stages, output / "pipeline.png", row)
