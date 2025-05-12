from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import cv2
import numpy as np
import utm

logger = logging.getLogger("app." + __name__)


# https://stackoverflow.com/a/2150512/185475
def shift(seq: list[Any], n: int) -> list[Any]:
    return seq[n:] + seq[:n]


class Fov:
    def __init__(self) -> None:
        logger.debug(f"Creating instance of Fov {self}")
        self.image_size: tuple[int, int]
        self.horizontal_fov: float
        self.vertical_fov: float
        self.camera_matrix: np.ndarray
        self.dist_coefficients: np.ndarray

    def set_image_size(self, width: int, height: int) -> None:
        self.image_size = (width, height)

    def set_camera_params(
        self,
        camera_matrix: np.ndarray,
        dist_coefficients: np.ndarray,
        horizontal_fov: float,
        vertical_fov: float,
        n_images: int | None = None,
    ) -> None:
        logger.debug("Setting camera params")
        self.camera_matrix = camera_matrix
        self.dist_coefficients = dist_coefficients
        self.horizontal_fov = horizontal_fov * np.pi / 180
        self.vertical_fov = vertical_fov * np.pi / 180

    @staticmethod
    def roll(roll: float) -> np.ndarray:
        return np.array(
            [
                [np.cos(roll), 0, np.sin(roll)],
                [0, 1, 0],
                [-np.sin(roll), 0, np.cos(roll)],
            ]
        )

    @staticmethod
    def pitch(pitch: float) -> np.ndarray:
        return np.array(
            [
                [1, 0, 0],
                [0, np.cos(pitch), -np.sin(pitch)],
                [0, np.sin(pitch), np.cos(pitch)],
            ]
        )

    @staticmethod
    def yaw(yaw: float) -> np.ndarray:
        return np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])

    def rotation(self, yaw: float, pitch: float, roll: float) -> np.ndarray:
        return np.matmul(self.yaw(yaw), np.matmul(self.pitch(pitch), self.roll(roll)))

    def get_unit_vector(self, image_point: tuple[float, float]) -> np.ndarray:
        if self.camera_matrix is not None:
            undist_point = cv2.undistortPoints(
                np.array([[image_point]], dtype=np.float32),
                self.camera_matrix,
                self.dist_coefficients,
                P=self.camera_matrix,
            )[0][0]
        else:
            undist_point = image_point
        image_center = np.array([self.image_size[0] / 2, self.image_size[1] / 2])
        image_point_from_center = undist_point - image_center
        image_plane_width_in_meters = np.tan(self.horizontal_fov / 2) * 2
        image_plane_height_in_meters = np.tan(self.vertical_fov / 2) * 2
        x = image_point_from_center[0] / self.image_size[0] * image_plane_width_in_meters
        y = 1
        z = -image_point_from_center[1] / self.image_size[1] * image_plane_height_in_meters
        vector = np.array([x, y, z])
        return vector

    def get_horizon_and_world_corners(
        self, world_point_dict: dict[Any, Any], yaw_pitch_roll: tuple[float, float, float]
    ) -> defaultdict[Any, list[dict[str, int]]]:
        margin = 200
        yaw_pitch_roll = (-yaw_pitch_roll[0], yaw_pitch_roll[1], yaw_pitch_roll[2])
        rotation_matrix = self.rotation(*yaw_pitch_roll)
        image_points = defaultdict(list)
        for direction, world_points in world_point_dict.items():
            temp_image_points_x = []
            temp_image_points_y = []
            for world_point in world_points:
                world_rotated_vector = np.matmul(np.transpose(rotation_matrix), world_point)
                if world_rotated_vector[1] >= 0:
                    vector = self.camera_matrix @ self.rotation(0, np.pi / 2, 0) @ world_rotated_vector
                    image_point_x = int(vector[0] / vector[2])
                    image_point_y = int(vector[1] / vector[2])
                    if (
                        -margin <= image_point_x <= self.image_size[0] + margin
                        and -margin <= image_point_y <= self.image_size[1] + margin
                    ):
                        temp_image_points_x.append(image_point_x)
                        temp_image_points_y.append(image_point_y)
            if temp_image_points_x != []:
                # Find last occurrence of the maximum x value
                name_id = len(temp_image_points_x) - 1 - temp_image_points_x[::-1].index(max(temp_image_points_x))
                # Reorder temp_image_points such that the largest x value is the first in the list.
                temp_image_points_x = shift(temp_image_points_x, name_id)
                temp_image_points_y = shift(temp_image_points_y, name_id)
            left = min(temp_image_points_x, default=0)
            top = min(temp_image_points_y, default=0)
            for x, y in zip(temp_image_points_x, temp_image_points_y, strict=False):
                image_points[direction].append({"x": x - left, "y": y - top})
            image_points[direction + "_pos"].append({"top": top, "left": left})
        return image_points

    def get_world_point(
        self,
        image_point: tuple[float, float],
        drone_height: float,
        yaw_pitch_roll: tuple[float, float, float],
        pos: tuple[float, float],
        return_zone: bool = False,
    ) -> tuple[np.ndarray, tuple[int, str]] | np.ndarray:
        unit_vector = self.get_unit_vector(image_point)
        yaw_pitch_roll = (-yaw_pitch_roll[0], yaw_pitch_roll[1], yaw_pitch_roll[2])
        rotation_matrix = self.rotation(*yaw_pitch_roll)
        rotated_vector = np.matmul(rotation_matrix, unit_vector)
        ground_vector = rotated_vector / rotated_vector[2] * -drone_height
        east_north_zone = self.convert_gps(*pos)
        world_point: np.ndarray = ground_vector[:2] + np.array(east_north_zone[:2])
        if return_zone:
            return world_point, east_north_zone[2:]
        else:
            return world_point

    def get_world_points(
        self,
        image_points: list[tuple[int, int]],
        drone_height: float,
        yaw_pitch_roll: tuple[float, float, float],
        pos: tuple[float, float],
    ) -> list[np.ndarray | tuple[np.ndarray, str]]:
        world_points = []
        for image_point in image_points:
            world_point = self.get_world_point(image_point, drone_height, yaw_pitch_roll, pos)
            world_points.append(world_point)
        return world_points

    def get_gps_point(
        self,
        image_point: tuple[int, int],
        drone_height: float,
        yaw_pitch_roll: tuple[float, float, float],
        pos: tuple[float, float],
    ) -> tuple[float, float]:
        world_point, zone = self.get_world_point(image_point, drone_height, yaw_pitch_roll, pos, True)
        lat, lon = self.convert_utm(world_point[0], world_point[1], zone)
        return lat, lon

    @staticmethod
    def convert_gps(lat: float, lon: float) -> tuple[float, float, int, str]:
        east_north_zone: tuple[float, float, int, str] = utm.from_latlon(lat, lon)
        return east_north_zone

    @staticmethod
    def convert_utm(east: float, north: float, zone: tuple[int, str]) -> tuple[float, float]:
        lat, lon = utm.to_latlon(east, north, *zone)
        return lat, lon


fov = Fov()
