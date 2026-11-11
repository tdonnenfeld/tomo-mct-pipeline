import numpy as np


def absorbance(normalized, floor=1e-6):
    return -np.log(np.maximum(normalized, np.float32(floor)))
