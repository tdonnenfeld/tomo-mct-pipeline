import numpy as np


def compare(reference, distorted):
    difference = distorted.astype(np.float64) - reference.astype(np.float64)
    rmse = float(np.sqrt(np.mean(difference**2)))
    mae = float(np.mean(np.abs(difference)))
    low, high = np.percentile(reference, [1, 99])
    scale = float(high - low)
    return {
        "rmse": rmse,
        "mae": mae,
        "nrmse": rmse / scale if scale else float("nan"),
        "psnr": float(20 * np.log10(scale / rmse)) if rmse and scale else float("inf"),
    }
