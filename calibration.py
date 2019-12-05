import os
import numpy as np
import cv2
import glob
import logging
from corner_detector import ChessBoardCornerDetector

logger = logging.getLogger('app.' + __name__)


class CalibrateCamera:
    def __init__(self):
        self.min_percentage_coverage = 50
        self.detector = ChessBoardCornerDetector()

    def detect_calibration_pattern_in_image(self, img):
        corners, coverage = self.detector.detect_chess_board_corners(img)
        obj_points = []
        img_points = []
        for key in corners.keys():
            for inner_key in corners[key].keys():
                obj_points.append(np.array([key, inner_key, 0]))
                img_points.append(corners[key][inner_key])
        return np.array(obj_points, dtype=np.float32), np.array(img_points, dtype=np.float32), coverage

    def calibrate_camera_from_images(self, image_files):
        obj_points_list = []
        img_points_list = []
        image_size = None
        for image_file in image_files:
            img = cv2.imread(image_file)
            image_size = (img.shape[1], img.shape[0])
            obj_points, img_points, coverage = self.detect_calibration_pattern_in_image(img)
            if coverage > self.min_percentage_coverage:
                obj_points_list.append(obj_points)
                img_points_list.append(img_points)
        if obj_points_list:
            _, mtx, dist, _, _ = cv2.calibrateCamera(obj_points_list, img_points_list, image_size, None, None)
            return mtx, dist, image_size
        else:
            return None, None, None

    def calibrate_camera_from_video(self, video_files):
        obj_points_list = []
        img_points_list = []
        image_size = None
        for video_file in video_files:
            cap = cv2.VideoCapture(video_file)
            count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    image_size = (frame.shape[1], frame.shape[0])
                    obj_points, img_points, coverage = self.detect_calibration_pattern_in_image(frame)
                    if coverage > self.min_percentage_coverage:
                        obj_points_list.append(obj_points)
                        img_points_list.append(img_points)
                        count += 30
                        cap.set(1, count)
                else:
                    break
            cap.release()
        if obj_points_list:
            _, mtx, dist, _, _ = cv2.calibrateCamera(obj_points_list, img_points_list, image_size, None, None)
            return mtx, dist, image_size
        else:
            return None, None, None

    @staticmethod
    def calculate_camera_fov(mtx, image_size):
        fov_x, fov_y, _, _, _ = cv2.calibrationMatrixValues(mtx, image_size, 1, 1)
        return fov_x, fov_y

    def __call__(self, in_folder, save_file, *args, **kwargs):
        logger.debug(f'Calibrating camera')
        image_files = []
        for file_format in ['*.jpg', '*.jpeg', '*.jpe', '*.bmp', '*.dib', '*.png', '*.tiff', '*.tif']:
            image_files.extend(glob.glob(os.path.join(in_folder, file_format)))
        video_files = []
        for file_format in ['*.mp4', '*.m4a', '*.m4v', '*.f4v', '*.f4a', '*.m4b', '*.m4r', '*.f4b', '*.mov', '*.wmv', '*.wma', '*.webm']:
            video_files.extend(glob.glob(os.path.join(in_folder, file_format)))
        if image_files:
            mtx, dist, image_size = self.calibrate_camera_from_images(image_files)
        elif video_files:
            mtx, dist, image_size = self.calibrate_camera_from_video(video_files)
        else:
            return
        if mtx is not None:
            fov_x, fov_y = self.calculate_camera_fov(mtx, image_size)
            np.savez(save_file, mtx=mtx, dist=dist, fov_x=fov_x, fov_y=fov_y)
            return True
        else:
            return -1
