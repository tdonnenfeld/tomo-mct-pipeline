import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


def roundtrip(projections, output, ratio, binaries):
    if projections.dtype != np.uint16 or projections.shape[0] % 4:
        raise ValueError("Expected uint16 projections in groups of four")
    output = Path(output)
    binaries = Path(binaries)
    output.mkdir(parents=True, exist_ok=True)
    count, height, width = projections.shape
    grouped = projections.reshape(count // 4, 4, height, width)
    components = grouped.transpose(1, 0, 2, 3).copy()
    component_height = count // 4 * height
    component_bytes = component_height * width * 2
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = f"{binaries}:{env.get('LD_LIBRARY_PATH', '')}"
    codestream = output / "compressed.j2c"
    with TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        input_path = temporary / "input.rawl"
        components.astype("<u2", copy=False).tofile(input_path)
        subprocess.run(
            [
                str(binaries / "kdu_compress"),
                "-i",
                f"{input_path}*4@{component_bytes}",
                "-o",
                str(codestream),
                f"Sdims={{{component_height},{width}}}",
                "Nprecision=16",
                "Nsigned=no",
                "Mcomponents=4",
                "Mprecision=16",
                "Msigned=no",
                "Sprecision=18",
                "Ssigned=yes",
                "Mvector_size:I4=4",
                "Mvector_coeffs:I4=32768",
                "Mstage_inputs:I25={0,3}",
                "Mstage_outputs:I25={0,3}",
                "Mstage_collections:I25={4,4}",
                "Mstage_xforms:I25={DWT,1,4,2,0}",
                "Mnum_stages=1",
                "Mstages=25",
                "Creversible=yes",
                "-precise",
                "-rate",
                str(64 / ratio),
            ],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
        )
        paths = [temporary / f"part{i}.rawl" for i in range(4)]
        subprocess.run(
            [
                str(binaries / "kdu_expand"),
                "-i",
                str(codestream),
                "-o",
                ",".join(map(str, paths)),
                "-precise",
            ],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
        )
        decoded_components = np.stack(
            [
                np.fromfile(path, dtype="<u2").reshape(count // 4, height, width)
                for path in paths
            ]
        )
    decoded = decoded_components.transpose(1, 0, 2, 3).reshape(projections.shape)
    return decoded, projections.nbytes / codestream.stat().st_size
