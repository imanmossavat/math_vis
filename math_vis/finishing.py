"""Final polish: grain, vignette, save, display."""
import numpy as np
from PIL import Image


def finish(
    img,
    name=None,
    grain=3.0,
    vignette=0.0,
    seed=0,
    display=True,
    download=False,
    width=520,
):
    """Apply grain/vignette, optionally save and display the image.

    Parameters
    ----------
    img : array-like
        (H, W, 3) image, values in 0..255.
    name : str, optional
        If given, the image is saved to this path.
    grain : float
        Standard deviation of Gaussian noise added to the image.
    vignette : float
        Strength of edge darkening (0 = none).
    seed : int
        Seed for the grain noise.
    display : bool
        If True and IPython is available, display the image inline.
    download : bool
        If True and running in Google Colab, trigger a browser download.
    width : int
        Display width in pixels.

    Returns
    -------
    np.ndarray
        The finished uint8 RGB image.
    """
    rng = np.random.default_rng(seed)
    img = np.asarray(img, dtype=np.float32)
    h, w = img.shape[:2]
    if vignette > 0:
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        img = img * (1 - vignette * np.clip(r - 0.6, 0, 1) ** 1.5)[..., None]
    if grain > 0:
        img = img + rng.normal(0, grain, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)

    if name is not None:
        Image.fromarray(img).save(name)

    if display:
        try:
            from IPython.display import Image as IPImage, display as ipy_display

            ipy_display(IPImage(data=array_to_bytes(img), width=width))
        except Exception:
            pass  # Not in an IPython environment

    if download and name is not None:
        try:
            from google.colab import files

            files.download(name)
        except Exception:
            pass

    return img


def array_to_bytes(img, fmt="png"):
    """Convert a uint8 RGB array to image bytes."""
    import io

    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=fmt)
    return buf.getvalue()
