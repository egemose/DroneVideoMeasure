from __future__ import annotations  # noqa: I001

import numpy as np

import pytest

from dvm.drone.fov import Fov


def test_set_camera_params() -> None:
    fov = Fov()
    mtx = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    fov_x = 58.330549
    fov_y = 32.815780
    fov.set_camera_params(mtx, dist, fov_x, fov_y, 1)
    assert fov.horizontal_fov == fov_x * np.pi / 180
    assert fov.vertical_fov == fov_y * np.pi / 180


def test_roll() -> None:
    fov = Fov()
    roll = 10
    roll_matrix = np.array(
        [
            [np.cos(roll), 0, np.sin(roll)],
            [0, 1, 0],
            [-np.sin(roll), 0, np.cos(roll)],
        ]
    )
    np.testing.assert_allclose(fov.roll(roll), roll_matrix)


def test_pitch() -> None:
    fov = Fov()
    pitch = 10
    pitch_matrix = np.array(
        [
            [1, 0, 0],
            [0, np.cos(pitch), -np.sin(pitch)],
            [0, np.sin(pitch), np.cos(pitch)],
        ]
    )
    np.testing.assert_allclose(fov.pitch(pitch), pitch_matrix)


def test_yaw() -> None:
    fov = Fov()
    yaw = 10
    yaw_matrix = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
    np.testing.assert_allclose(fov.yaw(yaw), yaw_matrix)


def test_rotation() -> None:
    fov = Fov()
    roll = 10
    pitch = 20
    yaw = 30
    rotation_matrix = np.array(
        [[-0.620145, 0.403198, 0.672942], [0.752418, 0.062947, 0.655671], [0.222005, 0.912945, -0.34241]]
    )
    np.testing.assert_allclose(fov.rotation(yaw, pitch, roll), rotation_matrix, rtol=1e-5)


def test_unit_vector() -> None:
    fov = Fov()
    mtx = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    fov_x = 58.330549
    fov_y = 32.815780
    fov.set_camera_params(mtx, dist, fov_x, fov_y, 1)
    fov.set_image_size(3000, 2000)
    unit_vector = fov.get_unit_vector((1000, 500))
    np.testing.assert_allclose(unit_vector, np.array([-0.1860306, 1, 0.1472286]))


def test_world_point() -> None:
    fov = Fov()
    mtx = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    fov_x = 58.330549
    fov_y = 32.815780
    fov.set_camera_params(mtx, dist, fov_x, fov_y, 1)
    fov.set_image_size(3000, 2000)
    image_points = [(500, 500), (1000, 1500)]
    world_points = fov.get_world_points(image_points, 10, (10, 20, 30), (55, 10))
    print(world_points)
    wp1 = np.array([563970.31116686, 6095257.9894299])
    wp2 = np.array([563972.48759115, 6095254.00068734])
    np.testing.assert_allclose(world_points[0], wp1)
    np.testing.assert_allclose(world_points[1], wp2)


def test_gps_point() -> None:
    fov = Fov()
    mtx = np.array([[1.83427403e03, 0, 9.87014485e02], [0, 1.83308269e03, 5.78589467e02], [0, 0, 1]])
    dist = np.array([[6.489003e-02, -6.948572e-01, -3.838770e-04, 8.868022e-04, 2.579142]])
    fov_x = 58.330549
    fov_y = 32.815780
    fov.set_camera_params(mtx, dist, fov_x, fov_y, 1)
    fov.set_image_size(3000, 2000)
    gps = fov.get_gps_point((1500, 1000), 20, (30, 20, 10), (55, 10))
    assert pytest.approx(gps[0], rel=1e-3) == 55
    assert pytest.approx(gps[1], rel=1e-3) == 10
