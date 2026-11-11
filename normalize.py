import numpy as np


def fields(flats, darks):
    return flats.mean(axis=0, dtype=np.float32), darks.mean(axis=0, dtype=np.float32)


def normalize(projections, flat, dark, cutoff=None):
    denominator = np.maximum(flat - dark, np.float32(1e-6))
    normalized = (projections.astype(np.float32) - dark) / denominator
    if cutoff is not None:
        np.minimum(normalized, cutoff, out=normalized)
    return normalized
