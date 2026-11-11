from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import tifffile


def load(source, kind):
    source = Path(source)
    if source.is_file():
        with ZipFile(source) as archive:
            names = sorted(
                name
                for name in archive.namelist()
                if f"PCO_EDGE_{kind}_data_" in name and name.endswith(".tiff")
            )
            if not names:
                raise ValueError(f"No {kind} images found in {source}")
            return np.stack(
                [tifffile.imread(BytesIO(archive.read(name))) for name in names]
            )
    names = sorted(source.rglob(f"PCO_EDGE_{kind}_data_*.tiff"))
    if not names:
        raise ValueError(f"No {kind} images found in {source}")
    return np.stack([tifffile.imread(name) for name in names])
