"""Image I/O helpers that embed generation metadata in PNG files.

The PNG ``tEXt`` chunk key ``generation`` stores a JSON object describing
the code, parameters, and commit that produced the image, so the asset can
always be traced back to its source.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
from PIL import Image, PngImagePlugin


def save_with_meta(
    img: np.ndarray,
    path: Union[str, Path],
    *,
    software: str = "math_vis",
    **metadata: Any,
) -> Path:
    """Save an RGB/RGBA uint8 image as PNG with embedded JSON metadata.

    Parameters
    ----------
    img : np.ndarray
        Image array of shape (H, W, 3) or (H, W, 4) and dtype uint8.
    path : str | Path
        Output path.
    software : str
        Identifier for the generating software/package.
    **metadata :
        Arbitrary key/value pairs describing the generation parameters.
        Values are JSON-serialised; non-serialisable values are coerced to str.

    Returns
    -------
    Path
        The resolved output path.
    """
    path = Path(path)
    if img.dtype != np.uint8:
        raise TypeError(f"Expected uint8 image, got {img.dtype}")
    if img.ndim not in (3, 4) or img.shape[-1] not in (3, 4):
        raise ValueError(f"Expected (H, W, 3/4) array, got shape {img.shape}")

    mode = "RGBA" if img.shape[-1] == 4 else "RGB"
    pil_img = Image.fromarray(img, mode=mode)

    pnginfo = PngImagePlugin.PngInfo()
    meta = {"software": software, **metadata}
    pnginfo.add_text(
        "generation",
        json.dumps(meta, indent=2, default=str),
        zip=True,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    pil_img.save(path, pnginfo=pnginfo, optimize=True)
    return path


def load_meta(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Return the JSON ``generation`` metadata from a PNG, if present."""
    with Image.open(path) as im:
        meta = im.info.get("generation")
    if meta is None:
        return None
    return json.loads(meta)
