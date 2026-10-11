import numpy as np
import math_vis as mv


def test_finish_shape_dtype():
    img = np.full((60, 80, 3), 128, dtype=np.float32)
    out = mv.finish(img, grain=0, vignette=0, display=False)
    assert out.shape == (60, 80, 3)
    assert out.dtype == np.uint8


def test_vignette_darkens_corners():
    img = np.full((100, 100, 3), 200, dtype=np.float32)
    out = mv.finish(img, grain=0, vignette=0.5, display=False)
    cx, cy = 50, 50
    corner = out[5, 5].mean()
    center = out[cy, cx].mean()
    assert corner < center


def test_grain_adds_noise():
    img = np.full((50, 50, 3), 128, dtype=np.float32)
    out = mv.finish(img, grain=10, vignette=0, display=False)
    assert out.std() > 0
