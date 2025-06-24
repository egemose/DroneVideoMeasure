from __future__ import annotations  # noqa: I001

from pathlib import Path

import pytest

import numpy as np

from flask.testing import FlaskClient

from dvm.calibration.calibration import CalibrateCamera
from dvm.calibration.corner_detector import ChessBoardCornerDetector


def test_init_calibrate_camera() -> None:
    cc = CalibrateCamera()
    assert isinstance(cc.detector, ChessBoardCornerDetector)


def test_calibrate_from_image(client: FlaskClient) -> None:
    cc = CalibrateCamera()
    image_files = [Path("./tests/test_data/calibration.jpg").resolve()]
    res = cc.calibrate_camera_from_images(image_files)
    if res is not None:
        mtx, dist, image_size, n_images = res
    mtx_test = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist_test = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    np.testing.assert_allclose(mtx, mtx_test)
    np.testing.assert_allclose(dist, dist_test, rtol=1e-6)
    assert image_size == (2048, 1080)
    assert n_images == 1


def test_calibrate_from_call(client: FlaskClient) -> None:
    cc = CalibrateCamera()
    image_files = Path("./tests/test_data/").resolve()
    res = cc(in_folder=image_files)
    if res is not None and not isinstance(res, int):
        mtx, dist, fov_x, fov_y, n_images = res
    mtx_test = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist_test = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    np.testing.assert_allclose(mtx, mtx_test)
    np.testing.assert_allclose(dist, dist_test, rtol=1e-6)
    assert pytest.approx(fov_x) == 58.330549
    assert pytest.approx(fov_y) == 32.815780
    assert n_images == 1
