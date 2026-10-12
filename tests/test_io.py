"""Tests for math_vis.io metadata helpers."""
import numpy as np
import pytest
from PIL import Image

from math_vis import save_with_meta, load_meta


def test_save_with_meta_round_trip(tmp_path):
    img = np.random.default_rng(0).integers(
        0, 256, size=(10, 12, 3), dtype=np.uint8
    )
    out = tmp_path / "out.png"
    meta = {
        "source": "test",
        "seed": 42,
        "params": {"warp": 16, "lead_px": 1.8},
    }
    saved = save_with_meta(img, out, **meta)
    assert saved == out
    assert out.exists()

    loaded = load_meta(out)
    assert loaded is not None
    assert loaded["software"] == "math_vis"
    assert loaded["source"] == "test"
    assert loaded["seed"] == 42
    assert loaded["params"] == meta["params"]

    # Pixel content is preserved.
    with Image.open(out) as im:
        assert np.array_equal(np.array(im), img)


def test_load_meta_returns_none_when_missing(tmp_path):
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    out = tmp_path / "plain.png"
    Image.fromarray(img).save(out)
    assert load_meta(out) is None


def test_save_with_meta_rejects_bad_dtype(tmp_path):
    img = np.zeros((4, 4, 3), dtype=np.float32)
    with pytest.raises(TypeError):
        save_with_meta(img, tmp_path / "bad.png")


def test_save_with_meta_rejects_bad_shape(tmp_path):
    img = np.zeros((4, 4), dtype=np.uint8)
    with pytest.raises(ValueError):
        save_with_meta(img, tmp_path / "bad.png")
