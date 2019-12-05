import cv2
import numpy as np
import MarkerTracker
import math
import collections
from sklearn.neighbors import KDTree


class ChessBoardCornerDetector:
    def __init__(self):
        self.distance_threshold = 0.06
        self.calibration_points = None
        self.points_to_examine_queue = None
        self.centers = None
        
    def detect_chess_board_corners(self, img):
        response = self.calculate_corner_responses(img)
        response_relative_to_neighbourhood = self.local_normalization(response, 511)
        relative_responses_threshold = self.threshold_responses(response_relative_to_neighbourhood)
        centers = self.locate_centers_of_peaks(relative_responses_threshold)
        selected_center = self.select_central_peak_location(centers)
        calibration_points = self.enumerate_peaks(centers, selected_center)
        percentage_image_covered = self.image_coverage(calibration_points, img)
        return self.calibration_points, percentage_image_covered

    @staticmethod
    def calculate_corner_responses(img):
        locator = MarkerTracker.MarkerTracker(order=2, kernel_size=45, scale_factor=40)
        greyscale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        response = locator.apply_convolution_with_complex_kernel(greyscale_image)
        return response

    def local_normalization(self, response, neighbourhood_size):
        _, max_val, _, _ = cv2.minMaxLoc(response)
        response_relative_to_neighbourhood = self.peaks_relative_to_neighbourhood(response, neighbourhood_size, 0.05 * max_val)
        return response_relative_to_neighbourhood

    @staticmethod
    def threshold_responses(response_relative_to_neighbourhood):
        _, relative_responses_threshold = cv2.threshold(response_relative_to_neighbourhood, 0.5, 255, cv2.THRESH_BINARY)
        return relative_responses_threshold

    def locate_centers_of_peaks(self, relative_responses_threshold):
        contours, _ = cv2.findContours(np.uint8(relative_responses_threshold), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        centers = list(map(self.get_center_of_mass, contours))
        return centers

    @staticmethod
    def select_central_peak_location(centers):
        mean_position_of_centers = np.mean(centers, axis=0)
        central_centers = np.array(sorted(list(centers), key=lambda c: np.sqrt((c[0] - mean_position_of_centers[0]) ** 2 + (c[1] - mean_position_of_centers[1]) ** 2)))
        return central_centers[0]

    def enumerate_peaks(self, centers, selected_center):
        self.centers = centers
        centers_kd_tree = KDTree(np.array(centers))
        self.calibration_points = self.initialize_calibration_points(selected_center, centers_kd_tree)
        self.points_to_examine_queue = [(0, 0), (1, 0), (0, 1)]
        for x_index, y_index in self.points_to_examine_queue:
            self.apply_all_rules_to_add_calibration_points(centers_kd_tree, x_index, y_index)
        return self.calibration_points

    def initialize_calibration_points(self, selected_center, centers_kdtree):
        closest_neighbour, _ = self.locate_nearest_neighbour(selected_center, centers_kdtree)
        direction = selected_center - closest_neighbour
        rotation_matrix = np.array([[0, 1], [-1, 0]])
        hat_vector = np.matmul(direction, rotation_matrix)
        direction_b_neighbour, _ = self.locate_nearest_neighbour(selected_center + hat_vector, centers_kdtree, minimum_distance_from_selected_center=-1)
        calibration_points = collections.defaultdict(dict)
        calibration_points[0][0] = selected_center
        calibration_points[1][0] = closest_neighbour
        calibration_points[0][1] = direction_b_neighbour
        return calibration_points

    def apply_all_rules_to_add_calibration_points(self, centers_kdtree, x_index, y_index):
        self.rule_one(centers_kdtree, x_index, y_index)
        self.rule_two(centers_kdtree, x_index, y_index)
        self.rule_three(centers_kdtree, x_index, y_index)
        self.rule_four(centers_kdtree, x_index, y_index)
        self.rule_five(centers_kdtree, x_index, y_index)

    def rule_three(self, centers_kdtree, x_index, y_index):
        try:
            if y_index + 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index - 1][y_index]
            position_two = self.calibration_points[x_index - 1][y_index + 1]
            position_three = self.calibration_points[x_index][y_index]
            predicted_location = position_two + position_three - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location, centers_kdtree, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_three - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index + 1] = location
                self.points_to_examine_queue.append((x_index, y_index + 1))
        except KeyError:
            pass

    def rule_two(self, centers_kdtree, x_index, y_index):
        try:
            if y_index in self.calibration_points[x_index + 1]:
                return
            position_one = self.calibration_points[x_index - 1][y_index]
            position_two = self.calibration_points[x_index][y_index]
            predicted_location = 2 * position_two - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location, centers_kdtree, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index + 1][y_index] = location
                self.points_to_examine_queue.append((x_index + 1, y_index))
        except KeyError:
            pass

    def rule_one(self, centers_kdtree, x_index, y_index):
        try:
            if y_index + 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index][y_index]
            position_two = self.calibration_points[x_index][y_index - 1]
            predicted_location = 2 * position_one - position_two
            location, distance = self.locate_nearest_neighbour(predicted_location, centers_kdtree, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index + 1] = location
                self.points_to_examine_queue.append((x_index, y_index + 1))
        except KeyError:
            pass

    def rule_four(self, centers_kdtree, x_index, y_index):
        try:
            if y_index - 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index][y_index]
            position_two = self.calibration_points[x_index][y_index + 1]
            predicted_location = 2 * position_one - position_two
            location, distance = self.locate_nearest_neighbour(predicted_location, centers_kdtree, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index - 1] = location
                self.points_to_examine_queue.append((x_index, y_index - 1))
        except KeyError:
            pass

    def rule_five(self, centers_kdtree, x_index, y_index):
        try:
            if y_index in self.calibration_points[x_index - 1]:
                return
            position_one = self.calibration_points[x_index + 1][y_index]
            position_two = self.calibration_points[x_index][y_index]
            predicted_location = 2 * position_two - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location, centers_kdtree, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index - 1][y_index] = location
                self.points_to_examine_queue.append((x_index - 1, y_index))
        except KeyError:
            pass

    def locate_nearest_neighbour(self, selected_center, centers_kdtree, minimum_distance_from_selected_center=0):
        reshaped_query_array = np.array(selected_center).reshape(1, -1)
        (distances, indices) = centers_kdtree.query(reshaped_query_array, 2)
        if distances[0][0] <= minimum_distance_from_selected_center:
            return self.centers[indices[0][1]], distances[0][1]
        else:
            return self.centers[indices[0][0]], distances[0][0]

    @staticmethod
    def distance_to_ref(ref_point):
        return lambda c: ((c[0] - ref_point[0]) ** 2 + (c[1] - ref_point[1]) ** 2) ** 0.5

    @staticmethod
    def get_center_of_mass(contour):
        m = cv2.moments(contour)
        if m["m00"] > 0:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
            result = np.array([cx, cy])
        else:
            result = np.array([contour[0][0][0], contour[0][0][1]])
        return result

    def peaks_relative_to_neighbourhood(self, response, neighbourhood_size, value_to_add):
        local_min_image = self.minimum_image_value_in_neighbourhood(response, neighbourhood_size)
        local_max_image = self.maximum_image_value_in_neighbourhood(response, neighbourhood_size)
        response_relative_to_neighbourhood = (response - local_min_image) / (
                value_to_add + local_max_image - local_min_image)
        return response_relative_to_neighbourhood

    @staticmethod
    def minimum_image_value_in_neighbourhood(response, neighbourhood_size):
        kernel_1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        orig_size = response.shape
        for x in range(int(math.log(neighbourhood_size, 2))):
            eroded_response = cv2.morphologyEx(response, cv2.MORPH_ERODE, kernel_1)
            response = cv2.resize(eroded_response, None, fx=0.5, fy=0.5)
        local_min_image_temp = cv2.resize(response, (orig_size[1], orig_size[0]))
        return local_min_image_temp

    @staticmethod
    def maximum_image_value_in_neighbourhood(response, neighbourhood_size):
        kernel_1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        orig_size = response.shape
        for x in range(int(math.log(neighbourhood_size, 2))):
            eroded_response = cv2.morphologyEx(response, cv2.MORPH_DILATE, kernel_1)
            response = cv2.resize(eroded_response, None, fx=0.5, fy=0.5)
        local_min_image_temp = cv2.resize(response, (orig_size[1], orig_size[0]))
        return local_min_image_temp

    @staticmethod
    def image_coverage(calibration_points, img):
        h = img.shape[0]
        w = img.shape[1]
        score = np.zeros((10, 10))
        for key in calibration_points.keys():
            for inner_key in calibration_points[key].keys():
                (x, y) = calibration_points[key][inner_key]
                (x_bin, x_rem) = divmod(x, w / 10)
                (y_bin, y_rem) = divmod(y, h / 10)
                if x_bin is 10:
                    x_bin = 9
                if y_bin is 10:
                    y_bin = 9
                score[int(x_bin)][int(y_bin)] += 1
        return np.count_nonzero(score)
