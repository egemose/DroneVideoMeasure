import numpy as np
import utm
import cv2
from collections import defaultdict


class Fov:
    def __init__(self):
        self.image_size = None
        self.horizontal_fov = None
        self.vertical_fov = None
        self.camera_matrix = None
        self.dist_coefficients = None
        self.camera_matrix = None
        self.dist_coefficients = None

    def set_image_size(self, width, height):
        self.image_size = (width, height)

    def set_camera_params(self, mat_file):
        mat_contents = np.load(mat_file)
        self.camera_matrix = np.transpose(mat_contents['mtx'])
        self.dist_coefficients = mat_contents['dist']
        self.horizontal_fov = mat_contents['fov_x'] * np.pi / 180
        self.vertical_fov = mat_contents['fov_y'] * np.pi / 180

    @staticmethod
    def roll(roll):
        return np.array([[np.cos(roll), 0, np.sin(roll)], [0, 1, 0], [-np.sin(roll), 0, np.cos(roll)]])

    @staticmethod
    def pitch(pitch):
        return np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])

    @staticmethod
    def yaw(yaw):
        return np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])

    def rotation(self, yaw, pitch, roll):
        return np.matmul(self.yaw(yaw), np.matmul(self.pitch(pitch), self.roll(roll)))

    def get_unit_vector(self, image_point):
        if self.camera_matrix is not None:
            undist_point = cv2.undistortPoints(np.array([[image_point]], dtype=np.float32), self.camera_matrix, self.dist_coefficients, P=self.camera_matrix)[0][0]
        else:
            undist_point = image_point
        image_center = np.array([self.image_size[0]/2, self.image_size[1]/2])
        image_point_from_center = undist_point - image_center
        image_plane_width_in_meters = np.tan(self.horizontal_fov/2)*2
        image_plane_height_in_meters = np.tan(self.vertical_fov/2)*2
        x = image_point_from_center[0] / self.image_size[0] * image_plane_width_in_meters
        y = 1
        z = - image_point_from_center[1] / self.image_size[1] * image_plane_height_in_meters
        vector = np.array([x, y, z])
        return vector

    @staticmethod
    def grouped(iterable, n):
        return zip(*[iter(iterable)] * n)

    def get_horizon_and_world_corners(self, world_point_dict, yaw_pitch_roll):
        margin = 200
        image_plane_width_in_meters = np.tan(self.horizontal_fov / 2) * 2
        image_plane_height_in_meters = np.tan(self.vertical_fov / 2) * 2
        yaw_pitch_roll = (-yaw_pitch_roll[0], yaw_pitch_roll[1], yaw_pitch_roll[2])
        rotation_matrix = self.rotation(*yaw_pitch_roll)
        image_points = defaultdict(list)
        for direction, world_points in world_point_dict.items():
            temp_image_points_x = []
            temp_image_points_y = []
            for world_point in world_points:
                world_rotated_vector = np.matmul(np.transpose(rotation_matrix), world_point)
                if world_rotated_vector[1] >= 0:
                    vector = world_rotated_vector / world_rotated_vector[1]
                    image_point_x = int(vector[0] / image_plane_width_in_meters * self.image_size[0] + self.image_size[0]/2)
                    image_point_y = int(- vector[2] / image_plane_height_in_meters * self.image_size[1] + self.image_size[1]/2)
                    if -margin <= image_point_x <= self.image_size[0] + margin:
                        if -margin <= image_point_y <= self.image_size[1] + margin:
                            temp_image_points_x.append(image_point_x)
                            temp_image_points_y.append(image_point_y)
            left = min(temp_image_points_x, default=0)
            top = min(temp_image_points_y, default=0)
            for x, y in zip(temp_image_points_x, temp_image_points_y):
                image_points[direction].append({'x': x - left, 'y': y - top})
            image_points[direction + '_pos'].append({'top': top, 'left': left})
        return image_points

    def get_world_point(self, image_point, drone_height, yaw_pitch_roll, pos, return_zone=False):
        unit_vector = self.get_unit_vector(image_point)
        yaw_pitch_roll = (-yaw_pitch_roll[0], yaw_pitch_roll[1], yaw_pitch_roll[2])
        rotation_matrix = self.rotation(*yaw_pitch_roll)
        rotated_vector = np.matmul(rotation_matrix, unit_vector)
        ground_vector = rotated_vector / rotated_vector[2] * -drone_height
        east_north_zone = self.convert_gps(*pos)
        world_point = ground_vector[:2] + np.array(east_north_zone[:2])
        if return_zone:
            return world_point, east_north_zone[2:]
        else:
            return world_point

    def get_world_points(self, image_points, drone_height, yaw_pitch_roll, pos):
        world_points = []
        for image_point in image_points:
            world_point = self.get_world_point(image_point, drone_height, yaw_pitch_roll, pos)
            world_points.append(world_point)
        return world_points

    def get_gps_point(self, image_point, drone_height, yaw_pitch_roll, pos):
        world_point, zone = self.get_world_point(image_point, drone_height, yaw_pitch_roll, pos, True)
        lat, lon = self.convert_utm(world_point[0], world_point[1], zone)
        return lat, lon

    @staticmethod
    def convert_gps(lat, lon):
        east_north_zone = utm.from_latlon(lat, lon)
        return east_north_zone

    @staticmethod
    def convert_utm(east, north, zone):
        lat, lon = utm.to_latlon(east, north, *zone)
        return lat, lon


fov = Fov()
