from sklearn.neighbors import KDTree
import numpy as np
from icecream import ic
import collections
import cv2

class PeakEnumerator():
    def __init__(self, centers):
        self.centers = centers
        self.central_peak_location = None
        self.distance_threshold = 0.06


    def select_central_peak_location(self):
        mean_position_of_centers = np.mean(
            self.centers, axis=0)
        
        central_center = np.array(
            sorted(list(self.centers), 
                   key=lambda c: np.sqrt((
                       c[0] - mean_position_of_centers[0]) ** 2 + 
                       (c[1] - mean_position_of_centers[1]) ** 2)))
        
        self.central_peak_location = central_center[0]
        return self.central_peak_location
    

    def enumerate_peaks(self):
        self.centers_kdtree = KDTree(np.array(self.centers))
        self.calibration_points = self.initialize_calibration_points(self.central_peak_location)
        self.enumerate_central_square()
        self.build_examination_queue()
        self.analyse_elements_in_queue()
        return self.calibration_points


    def initialize_calibration_points(self, selected_center):
        closest_neighbour, _ = self.locate_nearest_neighbour(selected_center)
        direction = selected_center - closest_neighbour
        rotation_matrix = np.array([[0, 1], [-1, 0]])
        hat_vector = np.matmul(direction, rotation_matrix)
        # Check if selected_center and direction_b_neighbour are identical.
        # If that is the case, search for a point further away.
        ratio = 1
        while True:
            direction_b_neighbour, _ = self.locate_nearest_neighbour(selected_center + hat_vector * ratio, minimum_distance_from_selected_center=-1)
            distance = np.linalg.norm(direction_b_neighbour - selected_center)
            if distance < 1:
                ratio = ratio + 0.3
            else:
                break

            if ratio > 2.5:
                ic(ratio)
                ic(selected_center)
                ic(closest_neighbour)
                ic(direction_b_neighbour)
                raise Exception("Square locator failed")
        calibration_points = collections.defaultdict(dict)
        calibration_points[0][0] = selected_center
        calibration_points[1][0] = closest_neighbour
        calibration_points[0][1] = direction_b_neighbour

        return calibration_points


    def enumerate_central_square(self):
        p00 = self.calibration_points[0][0]
        p01 = self.calibration_points[0][1]
        p10 = self.calibration_points[1][0]

        reference_distance = np.linalg.norm(p01 - p00)

        p11_expected_position = p01 + p10 - p00
        p11, distance = self.locate_nearest_neighbour(p11_expected_position)

        error_ratio = distance / reference_distance
        if error_ratio < 0.4:
            self.calibration_points[1][1] = p11
        else:
            ic(error_ratio)
            raise Exception("enumerate_central_square failed")
            pass
            # Throw error        


    def build_examination_queue(self):
        self.points_to_examine_queue = []
        for x_key, value in self.calibration_points.items():
            for y_key, _ in value.items():
                self.points_to_examine_queue.append((x_key, y_key))


    def analyse_elements_in_queue(self):
        for x_index, y_index in self.points_to_examine_queue:
            self.expand_calibration_grid(x_index, y_index)


    def expand_calibration_grid(self, x_index, y_index):
        # This rule tries to estimate the perspective distortion of four points
        # and then use this distortion model to locate new points of the 
        # chessboard pattern.
        try:
            p00 = self.calibration_points[x_index][y_index]
            p01 = self.calibration_points[x_index][y_index + 1]
            p10 = self.calibration_points[x_index + 1][y_index]
            p11 = self.calibration_points[x_index + 1][y_index + 1]
        except Exception as e:
            #print(e)
            return

        reference_distance = np.linalg.norm(p01 - p00)

        src = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], 
                       dtype=float)
        dst = np.array([p00, p01, p10, p11], 
                       dtype=float)

        H, _mask = cv2.findHomography(src, dst)

        self.search_for_point(x_index, y_index, reference_distance, H, (0, 2))
        self.search_for_point(x_index, y_index, reference_distance, H, (1, 2))
        self.search_for_point(x_index, y_index, reference_distance, H, (2, 1))
        self.search_for_point(x_index, y_index, reference_distance, H, (2, 0))
        self.search_for_point(x_index, y_index, reference_distance, H, (1, -1))
        self.search_for_point(x_index, y_index, reference_distance, H, (0, -1))
        self.search_for_point(x_index, y_index, reference_distance, H, (-1, 0))
        self.search_for_point(x_index, y_index, reference_distance, H, (-1, 1))


    def search_for_point(self, x_index, y_index, reference_distance, H, point):
        x_idx = x_index + point[0]
        y_idx = y_index + point[1]

        if y_idx not in self.calibration_points[x_idx]:
            pxx = H @ np.array([[point[0]], [point[1]], [1]])
            pxx = pxx / pxx[2]
            location, distance = self.locate_nearest_neighbour(pxx[0:2],
                                                               minimum_distance_from_selected_center=-1)
            if distance / reference_distance < self.distance_threshold:
                #ic(distance / reference_distance)
                self.calibration_points[x_idx][y_idx] = location
                self.points_to_examine_queue.append((x_idx, y_idx))


    def locate_nearest_neighbour(self, selected_center, minimum_distance_from_selected_center=0):
        reshaped_query_array = np.array(selected_center).reshape(1, -1)
        (distances, indices) = self.centers_kdtree.query(reshaped_query_array, 2)
        if distances[0][0] <= minimum_distance_from_selected_center:
            return self.centers[indices[0][1]], distances[0][1]
        else:
            return self.centers[indices[0][0]], distances[0][0]

