import cv2
import numpy as np
from calibration.MarkerTracker import MarkerTracker
import math
import collections
from sklearn.neighbors import KDTree


class ChessBoardCornerDetector:
    def __init__(self):
        self.distance_threshold = 0.06
        self.calibration_points = None
        self.centers = None
        self.centers_kdtree = None
        self.points_to_examine_queue = None

    def detect_chess_board_corners(self, img, debug=False, *, path_to_image=None, path_to_output_folder=None):
        # Calculate corner responses
        response = self.calculate_corner_responses(img)
        # print("%8.2f, convolution" % (time.time() - t_start))
        # Localized normalization of responses
        response_relative_to_neighbourhood = self.local_normalization(response, 511)
        # print("%8.2f, relative response" % (time.time() - t_start))
        # Threshold responses
        relative_responses_thresholded = self.threshold_responses(response_relative_to_neighbourhood)
        # Locate centers of peaks
        centers = self.locate_centers_of_peaks(relative_responses_thresholded)
        # Select central center of mass
        selected_center = self.select_central_peak_location(centers)
        # Enumerate detected peaks
        calibration_points = self.enumerate_peaks(centers, selected_center)
        # print("%8.2f, grid mapping" % (time.time() - t_start))
        # write output images if debug is True
        if debug:
            # making the output folders
            path_to_output_local_maxima_folder = path_to_output_folder / '4_local_maxima'
            path_to_output_local_maxima_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_response_folder = path_to_output_folder / '1_response'
            path_to_output_response_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_response_neighbourhood_folder = path_to_output_folder / '2_respond_relative_to_neighbourhood'
            path_to_output_response_neighbourhood_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_response_threshold_folder = path_to_output_folder / '3_relative_response_thresholded'
            path_to_output_response_threshold_folder.mkdir(parents=False, exist_ok=True)
            path_response_1 = path_to_output_response_folder / (path_to_image.stem + '_response.png')
            cv2.imwrite(str(path_response_1), response)
            path_response_2 = path_to_output_response_neighbourhood_folder / (path_to_image.stem + '_response_relative_to_neighbourhood.png')
            cv2.imwrite(str(path_response_2), response_relative_to_neighbourhood * 255)
            path_response_3 = path_to_output_response_threshold_folder / (path_to_image.stem + '_relative_responses_thresholded.png')
            cv2.imwrite(str(path_response_3), relative_responses_thresholded)
            canvas = self.show_detected_calibration_points(img, self.calibration_points)
            cv2.circle(canvas, tuple(selected_center.astype(int)), 10, (0, 0, 255), -1)
            path_local_max = path_to_output_local_maxima_folder / (path_to_image.stem + '_local_maxima.png')
            cv2.imwrite(str(path_local_max), canvas)
        # Detect image covered
        percentage_image_covered = self.image_coverage(calibration_points, img)
        # How straight are the points?
        stats = self.statistics(calibration_points)
        return self.calibration_points, percentage_image_covered, stats

        # Not necessary to output the images when we just want the statistics after undistorting
    def make_statistics(self, img):
        # Calculate corner responses
        response = self.calculate_corner_responses(img)
        # Localized normalization of responses
        response_relative_to_neighbourhood = self.local_normalization(response, 511)
        # Threshold responses
        relative_responses_thresholded = self.threshold_responses(response_relative_to_neighbourhood)
        # Locate centers of peaks
        centers = self.locate_centers_of_peaks(relative_responses_thresholded)
        # Select central center of mass
        selected_center = self.select_central_peak_location(centers)
        # Enumerate detected peaks
        calibration_points = self.enumerate_peaks(centers, selected_center)
        # How straight are the points?
        stats = self.statistics(calibration_points)
        return stats

    @staticmethod
    def calculate_corner_responses(img):
        locator = MarkerTracker(order=2, kernel_size=45, scale_factor=40)
        greyscale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        response = locator.apply_convolution_with_complex_kernel(greyscale_image)
        return response

    def local_normalization(self, response, neighbourhoodsize):
        _, max_val, _, _ = cv2.minMaxLoc(response)
        response_relative_to_neighbourhood = self.peaks_relative_to_neighbourhood(response, neighbourhoodsize, 0.05 * max_val)
        return response_relative_to_neighbourhood

    @staticmethod
    def threshold_responses(response_relative_to_neighbourhood):
        _, relative_responses_thresholded = cv2.threshold(response_relative_to_neighbourhood, 0.5, 255, cv2.THRESH_BINARY)
        return relative_responses_thresholded

    def locate_centers_of_peaks(self, relative_responses_thresholded):
        contours, t1 = cv2.findContours(np.uint8(relative_responses_thresholded), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        centers = list(map(self.get_center_of_mass, contours))
        return centers

    @staticmethod
    def select_central_peak_location(centers):
        mean_position_of_centers = np.mean(centers, axis=0)
        central_center = np.array(sorted(list(centers), key=lambda c: np.sqrt((c[0] - mean_position_of_centers[0]) ** 2 + (c[1] - mean_position_of_centers[1]) ** 2)))
        return central_center[0]

    def enumerate_peaks(self, centers, selected_center):
        self.centers = centers
        self.centers_kdtree = KDTree(np.array(self.centers))
        self.calibration_points = self.initialize_calibration_points(selected_center)
        self.points_to_examine_queue = [(0, 0), (1, 0), (0, 1)]
        for x_index, y_index in self.points_to_examine_queue:
            self.apply_all_rules_to_add_calibration_points(x_index, y_index)
        return self.calibration_points

    @staticmethod
    def show_detected_calibration_points(img, calibration_points):
        canvas = img.copy()
        for x_index, temp in calibration_points.items():
            for y_index, cal_point in temp.items():
                cv2.circle(canvas, tuple(cal_point.astype(int)), 20, (0, 255 * (y_index % 2), 255 * (x_index % 2)), 2)
        return canvas 

    def initialize_calibration_points(self, selected_center):
        closest_neighbour, _ = self.locate_nearest_neighbour(selected_center)
        direction = selected_center - closest_neighbour
        rotation_matrix = np.array([[0, 1], [-1, 0]])
        hat_vector = np.matmul(direction, rotation_matrix)
        direction_b_neighbour, _ = self.locate_nearest_neighbour(selected_center + hat_vector, minimum_distance_from_selected_center=-1)
        calibration_points = collections.defaultdict(dict)
        calibration_points[0][0] = selected_center
        calibration_points[1][0] = closest_neighbour
        calibration_points[0][1] = direction_b_neighbour

        return calibration_points

    def apply_all_rules_to_add_calibration_points(self, x_index, y_index):
        self.rule_one(x_index, y_index)
        self.rule_two(x_index, y_index)
        self.rule_three(x_index, y_index)
        self.rule_four(x_index, y_index)
        self.rule_five(x_index, y_index)

    def rule_three(self, x_index, y_index):
        try:
            # Ensure that we don't overwrite already located
            # points.
            if y_index + 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index - 1][y_index]
            position_two = self.calibration_points[x_index - 1][y_index + 1]
            position_three = self.calibration_points[x_index][y_index]
            predicted_location = position_two + position_three - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location,
                                                               minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_three - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index + 1] = location
                self.points_to_examine_queue.append((x_index, y_index + 1))
        except KeyError:
            pass

    def rule_two(self, x_index, y_index):
        try:
            if y_index in self.calibration_points[x_index + 1]:
                return
            position_one = self.calibration_points[x_index - 1][y_index]
            position_two = self.calibration_points[x_index][y_index]
            predicted_location = 2 * position_two - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location,
                                                               minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index + 1][y_index] = location
                self.points_to_examine_queue.append((x_index + 1, y_index))
        except KeyError:
            pass

    def rule_one(self, x_index, y_index):
        try:
            # Ensure that we don't overwrite already located
            # points.
            if y_index + 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index][y_index]
            position_two = self.calibration_points[x_index][y_index - 1]
            predicted_location = 2 * position_one - position_two
            location, distance = self.locate_nearest_neighbour(predicted_location,
                                                               minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index + 1] = location
                self.points_to_examine_queue.append((x_index, y_index + 1))
        except KeyError:
            pass

    def rule_four(self, x_index, y_index):
        try:
            # Ensure that we don't overwrite already located
            # points.
            if y_index - 1 in self.calibration_points[x_index]:
                return
            position_one = self.calibration_points[x_index][y_index]
            position_two = self.calibration_points[x_index][y_index + 1]
            predicted_location = 2 * position_one - position_two
            location, distance = self.locate_nearest_neighbour(predicted_location,
                                                               minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index][y_index - 1] = location
                self.points_to_examine_queue.append((x_index, y_index - 1))
        except KeyError:
            pass

    def rule_five(self, x_index, y_index):
        try:
            if y_index in self.calibration_points[x_index - 1]:
                return

            position_one = self.calibration_points[x_index + 1][y_index]
            position_two = self.calibration_points[x_index][y_index]
            predicted_location = 2 * position_two - position_one
            location, distance = self.locate_nearest_neighbour(predicted_location, minimum_distance_from_selected_center=-1)
            reference_distance = np.linalg.norm(position_two - position_one)
            if distance / reference_distance < self.distance_threshold:
                self.calibration_points[x_index - 1][y_index] = location
                self.points_to_examine_queue.append((x_index - 1, y_index))
        except KeyError:
            pass

    def locate_nearest_neighbour(self, selected_center, minimum_distance_from_selected_center=0):
        reshaped_query_array = np.array(selected_center).reshape(1, -1)
        (distances, indices) = self.centers_kdtree.query(reshaped_query_array, 2)
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

    def peaks_relative_to_neighbourhood(self, response, neighbourhoodsize, value_to_add):
        local_min_image = self.minimum_image_value_in_neighbourhood(response, neighbourhoodsize)
        local_max_image = self.maximum_image_value_in_neighbourhood(response, neighbourhoodsize)
        response_relative_to_neighbourhood = (response - local_min_image) / (value_to_add + local_max_image - local_min_image)
        return response_relative_to_neighbourhood

    @staticmethod
    def minimum_image_value_in_neighbourhood(response, neighbourhood_size):
        """
        A fast method for determining the local minimum value in
        a neighbourhood for an entire image.
        """
        kernel_1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        orig_size = response.shape
        for x in range(int(math.log(neighbourhood_size, 2))):
            eroded_response = cv2.morphologyEx(response, cv2.MORPH_ERODE, kernel_1)
            response = cv2.resize(eroded_response, None, fx=0.5, fy=0.5)
        local_min_image_temp = cv2.resize(response, (orig_size[1], orig_size[0]))
        return local_min_image_temp

    @staticmethod
    def maximum_image_value_in_neighbourhood(response, neighbourhood_size):
        """
        A fast method for determining the local maximum value in
        a neighbourhood for an entire image.
        """
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
        for calibration_point_dict in calibration_points.values():
            for x, y in calibration_point_dict.values():
                (x_bin, x_rem) = divmod(x, w / 10)
                (y_bin, y_rem) = divmod(y, h / 10)
                if x_bin is 10:
                    x_bin = 9
                if y_bin is 10:
                    y_bin = 9
                score[int(x_bin)][int(y_bin)] += 1
        return np.count_nonzero(score)

    @staticmethod
    def shortest_distance(x1, y1, a, b, c):
        d = abs((a * x1 + b * y1 + c)) / (math.sqrt(a * a + b * b))
        return d

    def statistics(self, points):
        # Make a list in which we will return the statistics. This list will be contain two elements, each a tuple.
        # The first tuple is the amount of tested points and average pixel deviation from straight lines for the
        # horizontal points, the second tuple is the same for the vertical points.
        return_list = []
        # Check if the outer key defines the rows or the columns, this is not always the same.
        horizontal = 1 if points[0][0][0] - points[0][1][0] < points[0][0][1] - points[0][1][1] else 0
        # Flip the dictionary so we can do this statistic for horizontal and vertical points.
        flipped = collections.defaultdict(dict)
        for key, val in points.items():
            for subkey, subval in val.items():
                flipped[subkey][key] = subval
        # Make sure that we always have the same order, horizontal first in this case.
        horiz_first = (points, flipped) if horizontal else (flipped, points)
        for index, points_list in enumerate(horiz_first):
            count, som = 0, 0
            for k in points_list.values():
                single_col_x, single_col_y = [], []
                if len(k) > 2:
                    for l in k.values():
                        # for the vertical points, X and Y values are switched because polyfit
                        # does not work (well) for points (almost) vertical points
                        if index == 0:
                            single_col_x.append(l[0])
                            single_col_y.append(l[1])
                        else:
                            single_col_x.append(l[1])
                            single_col_y.append(l[0])
                    # Fit a line through the horizontal or vertical points
                    z = np.polynomial.polynomial.polyfit(single_col_x, single_col_y, 1)
                    # Calculate the distance for each point to the line
                    for x, y in zip(single_col_x, single_col_y):
                        d = self.shortest_distance(x, y, z[1], -1, z[0])
                        count += 1
                        som += d
            if count is not 0:
                return_list.append([count, som/count])
            else:
                return_list.append([count, 0])
        return return_list
