import cv2
import numpy as np
from dvm.calibration.MarkerTracker import MarkerTracker
import math
import time
import collections
import logging
from sklearn.neighbors import KDTree
from icecream import ic
from dvm.calibration.peak_enumerator import PeakEnumerator

logger = logging.getLogger("app." + __name__)


class ChessBoardCornerDetector:
    def __init__(self):
        self.distance_scale_ratio = 0.1
        self.distance_scale = 250
        self.distance_threshold = 0.13
        self.kernel_size = 101
        self.relative_threshold_level = 0.5
        self.calibration_points = None
        self.centers = None
        self.centers_kdtree = None
        self.points_to_examine_queue = None

    def detect_chess_board_corners(
        self, img, debug=False, *, path_to_image=None, path_to_output_folder=None
    ):
        try:
            # Calculate corner response
            response = self.calculate_corner_responses(img)
            # print("%8.2f, convolution" % (time.time() - t_start))
            # Localized normalization of responses
            response_relative_to_neighbourhood = self.local_normalization(
                response, self.distance_scale
            )
            # print("%8.2f, relative response" % (time.time() - t_start))
            # Threshold responses
            relative_responses_thresholded = self.threshold_responses(
                response_relative_to_neighbourhood
            )
            # Locate centers of peaks
            centers = self.locate_centers_of_peaks(relative_responses_thresholded)

            pe = PeakEnumerator(centers)
            selected_center = pe.select_central_peak_location()
            calibration_points = pe.enumerate_peaks()
            self.calibration_points = calibration_points
            # print("%8.2f, grid mapping" % (time.time() - t_start))
            # write output images if debug is True
        except Exception as e:
            print("Something failed in <detect_chess_board_corners>")
            ic(e)
        if debug:
            # Make output folders
            path_to_output_response_folder = path_to_output_folder / "1_response"
            path_to_output_response_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_response_neighbourhood_folder = (
                path_to_output_folder / "2_respond_relative_to_neighbourhood"
            )
            path_to_output_response_neighbourhood_folder.mkdir(
                parents=False, exist_ok=True
            )
            path_to_output_response_threshold_folder = (
                path_to_output_folder / "3_relative_response_thresholded"
            )
            path_to_output_response_threshold_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_located_centers_folder = (
                path_to_output_folder / "4_located_centers"
            )
            path_to_output_located_centers_folder.mkdir(parents=False, exist_ok=True)
            path_to_output_local_maxima_folder = (
                path_to_output_folder / "5_local_maxima"
            )
            path_to_output_local_maxima_folder.mkdir(parents=False, exist_ok=True)
            # Write debug images
            path_response_1 = path_to_output_response_folder / (
                path_to_image.stem + "_response.png"
            )
            cv2.imwrite(str(path_response_1), response)
            path_response_2 = path_to_output_response_neighbourhood_folder / (
                path_to_image.stem + "_response_relative_to_neighbourhood.png"
            )
            cv2.imwrite(str(path_response_2), response_relative_to_neighbourhood * 255)
            path_response_3 = path_to_output_response_threshold_folder / (
                path_to_image.stem + "_relative_responses_thresholded.png"
            )
            cv2.imwrite(str(path_response_3), relative_responses_thresholded)
            located_centers = self.show_detected_points(img, centers)
            path_response_4 = path_to_output_located_centers_folder / (
                path_to_image.stem + "_located_centers.png"
            )
            cv2.imwrite(str(path_response_4), located_centers)
            canvas = self.show_detected_calibration_points(img, self.calibration_points)
            cv2.circle(canvas, tuple(selected_center.astype(int)), 10, (0, 0, 255), -1)
            path_local_max = path_to_output_local_maxima_folder / (
                path_to_image.stem + "_local_maxima.png"
            )
            cv2.imwrite(str(path_local_max), canvas)
        
        try:
            # Detect image coverage
            percentage_image_covered = self.image_coverage(calibration_points, img)
            # How straight are the points?
            stats = self.statistics(calibration_points)
            return self.calibration_points, percentage_image_covered, stats
        except Exception as e:
            raise Exception("calibration_points was probably not calculated")

        # Not necessary to output the images when we just want the statistics after undistorting

    def make_statistics(self, img, debug, output, fname):
        # Calculate corner responses
        response = self.calculate_corner_responses(img)
        if debug:
            path_to_output_undistorted_corner_response = (
                output.parent / "91_undistorted_corner_response"
            )
            path_to_output_undistorted_corner_response.mkdir(
                parents=False, exist_ok=True
            )
            cv2.imwrite(
                path_to_output_undistorted_corner_response / (fname.stem + ".png"),
                response,
            )

        # Localized normalization of responses
        response_relative_to_neighbourhood = self.local_normalization(
            response, self.distance_scale
        )
        if debug:
            path_to_output_undistorted_response = (
                output.parent / "92_undistorted_relative_response"
            )
            path_to_output_undistorted_response.mkdir(parents=False, exist_ok=True)
            cv2.imwrite(
                path_to_output_undistorted_response / (fname.stem + ".png"),
                response_relative_to_neighbourhood * 255,
            )

        # Threshold responses
        relative_responses_thresholded = self.threshold_responses(
            response_relative_to_neighbourhood
        )
        if debug:
            path_to_output_undistorted_thresholded = (
                output.parent / "93_undistorted_thresholded"
            )
            path_to_output_undistorted_thresholded.mkdir(parents=False, exist_ok=True)
            cv2.imwrite(
                path_to_output_undistorted_thresholded / (fname.stem + ".png"),
                relative_responses_thresholded,
            )

        # Locate centers of peaks
        centers = self.locate_centers_of_peaks(relative_responses_thresholded)
        centers = sorted(centers, key=lambda item: item[0])
        # ic(centers)

        pe = PeakEnumerator(centers)
        selected_center = pe.select_central_peak_location()
        calibration_points = pe.enumerate_peaks()
        self.calibration_points = calibration_points

        if debug:
            canvas = self.show_detected_calibration_points(img, self.calibration_points)
            cv2.circle(canvas, tuple(selected_center.astype(int)), 10, (0, 0, 255), -1)
            path_to_output_undistorted_calibration_points = (
                output.parent / "95_undistorted_calibration_points"
            )
            path_to_output_undistorted_calibration_points.mkdir(
                parents=False, exist_ok=True
            )
            cv2.imwrite(
                path_to_output_undistorted_calibration_points / (fname.stem + ".png"),
                canvas,
            )

        # How straight are the points?
        stats = self.statistics(calibration_points)
        return stats

    def calculate_corner_responses(self, img):
        locator = MarkerTracker(order=2, kernel_size=self.kernel_size, scale_factor=40)
        greyscale_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        response = locator.apply_convolution_with_complex_kernel(greyscale_image)
        return response

    def local_normalization(self, response, neighbourhoodsize):
        _, max_val, _, _ = cv2.minMaxLoc(response)
        response_relative_to_neighbourhood = self.peaks_relative_to_neighbourhood(
            response, neighbourhoodsize, 0.05 * max_val
        )
        return response_relative_to_neighbourhood

    def threshold_responses(self, response_relative_to_neighbourhood):
        _, relative_responses_thresholded = cv2.threshold(
            response_relative_to_neighbourhood,
            self.relative_threshold_level,
            255,
            cv2.THRESH_BINARY,
        )
        return relative_responses_thresholded

    def locate_centers_of_peaks(self, relative_responses_thresholded):
        contours, t1 = cv2.findContours(
            np.uint8(relative_responses_thresholded),
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        centers = []
        for contour in contours:
            val = self.get_center_of_mass(contour)

            area = cv2.contourArea(contour)
            if area > 0:
                perimeter = cv2.arcLength(contour, closed=True)
                measure = 4 * np.pi * area / (perimeter * perimeter)
                if measure > 0.6:
                    centers.append(val)
        return centers

    def show_detected_points(self, img, points):
        canvas = img.copy()
        for point in points:
            x = int(point[0])
            y = int(point[1])
            cv2.circle(canvas, (x, y), int(self.kernel_size / 2), (0, 0, 255), 2)

        return canvas

    def show_detected_calibration_points(self, img, calibration_points):
        canvas = img.copy()
        for x_index, temp in calibration_points.items():
            for y_index, cal_point in temp.items():
                line_width = 1 + int(self.kernel_size / 100)
                cv2.circle(
                    canvas,
                    tuple(cal_point.astype(int)),
                    int(self.kernel_size / 2),
                    (0, 255 * (y_index % 2), 255 * (x_index % 2)),
                    line_width,
                )

                if x_index + 1 in self.calibration_points:
                    if y_index + 1 in self.calibration_points[x_index + 1]:
                        other_corner = self.calibration_points[x_index + 1][y_index + 1]
                        alpha = 0.3
                        p1 = alpha * cal_point + (1 - alpha) * other_corner
                        p2 = (1 - alpha) * cal_point + alpha * other_corner
                        cv2.line(
                            canvas,
                            tuple(p1.astype(int)),
                            tuple(p2.astype(int)),
                            (0, 0, 255),
                            line_width,
                        )
                if x_index + 1 in self.calibration_points:
                    if y_index - 1 in self.calibration_points[x_index + 1]:
                        other_corner = self.calibration_points[x_index + 1][y_index - 1]
                        alpha = 0.3
                        p1 = alpha * cal_point + (1 - alpha) * other_corner
                        p2 = (1 - alpha) * cal_point + alpha * other_corner
                        cv2.line(
                            canvas,
                            tuple(p1.astype(int)),
                            tuple(p2.astype(int)),
                            (0, 0, 255),
                            line_width,
                        )
        return canvas

    @staticmethod
    def distance_to_ref(ref_point):
        return (
            lambda c: ((c[0] - ref_point[0]) ** 2 + (c[1] - ref_point[1]) ** 2) ** 0.5
        )

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

    def peaks_relative_to_neighbourhood(
        self, response, neighbourhoodsize, value_to_add
    ):
        local_min_image = self.minimum_image_value_in_neighbourhood(
            response, neighbourhoodsize
        )
        local_max_image = self.maximum_image_value_in_neighbourhood(
            response, neighbourhoodsize
        )
        response_relative_to_neighbourhood = (response - local_min_image) / (
            value_to_add + local_max_image - local_min_image
        )
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

        # Calculate coverage of detected calibration as
        # a fraction of the image area.
        points = []
        for calibration_point_dict in calibration_points.values():
            for x, y in calibration_point_dict.values():
                points.append((x, y))
        points = np.array(points).reshape(-1, 1, 2).astype(np.float32)
        convexHull = cv2.convexHull(points)
        convexHullArea = cv2.contourArea(convexHull)
        imageArea = h * w
        coverage_ratio = convexHullArea / imageArea
        # ic(coverage_ratio)

        score = np.zeros((10, 10))
        for calibration_point_dict in calibration_points.values():
            for x, y in calibration_point_dict.values():
                (x_bin, x_rem) = divmod(x, w / 10)
                (y_bin, y_rem) = divmod(y, h / 10)
                if x_bin == 10:
                    x_bin = 9
                if y_bin == 10:
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
        horizontal = (
            1
            if points[0][0][0] - points[0][1][0] < points[0][0][1] - points[0][1][1]
            else 0
        )
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
            if count != 0:
                return_list.append([count, som / count])
            else:
                return_list.append([count, 0])
        return return_list
