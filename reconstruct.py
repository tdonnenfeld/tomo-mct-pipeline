from importlib.util import find_spec

import numpy as np


def reconstruct(
    absorbance, center, size, backend, preview_angles=500, preview_detectors=512
):
    if backend == "auto":
        backend = "tomopy" if find_spec("tomopy") else "skimage"
    n, rows, width = absorbance.shape
    theta = np.linspace(0, np.pi, n, endpoint=False, dtype=np.float32)
    if backend == "tomopy":
        import tomopy

        volume = tomopy.recon(absorbance, theta, center=center, algorithm="gridrec")
        if size != width:
            start = (width - size) // 2
            volume = volume[:, start : start + size, start : start + size]
    elif backend == "skimage":
        from scipy.ndimage import shift
        from skimage.transform import iradon

        if (
            preview_detectors > width
            or width % preview_detectors
            or size > preview_detectors
        ):
            raise ValueError(
                "Preview detector count must divide the original width and be >= output size"
            )
        indices = np.linspace(0, n - 1, min(n, preview_angles), dtype=int)
        binning = width // preview_detectors
        reduced = (
            absorbance[indices]
            .reshape(len(indices), rows, preview_detectors, binning)
            .mean(axis=-1)
        )
        offset = ((width - 1) / 2 - center) / binning
        angles = np.rad2deg(theta[indices])
        volume = np.stack(
            [
                iradon(
                    shift(
                        reduced[:, row, :],
                        (0, offset),
                        order=1,
                        mode="nearest",
                        prefilter=False,
                    ).T,
                    theta=angles,
                    circle=True,
                    filter_name="ramp",
                    output_size=size,
                ).astype(np.float32)
                for row in range(rows)
            ]
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")
    return volume, backend
