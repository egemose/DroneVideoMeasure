import os
import numpy as np
import cv2
import glob
from tqdm import tqdm


class CalibrateCamera:
    def __init__(self, checkerboard_size, *, show_progress=False):
        self.checkerboard_size = checkerboard_size
        self.show_progress = show_progress
        self.checkerboard = self._create_checkerboard()
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.obj_points = []
        self.image_points = []
        self.image_size = None

    def _create_checkerboard(self):
        obj_p = np.zeros((self.checkerboard_size[0] * self.checkerboard_size[1], 3), np.float32)
        obj_p[:, :2] = np.mgrid[0:self.checkerboard_size[0], 0:self.checkerboard_size[1]].T.reshape(-1, 2)
        return obj_p

    def _detect_checkerboard(self, folder, show_detections=False):
        gray = None
        image_files = glob.glob(os.path.join(folder, '*.jpg'))
        for image_file in tqdm(image_files, disable=not self.show_progress):
            image = cv2.imread(image_file)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.checkerboard_size, None)
            if ret:
                self.obj_points.append(self.checkerboard)
                new_corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                self.image_points.append(new_corners)
                if show_detections:
                    cv2.drawChessboardCorners(image, self.checkerboard_size, new_corners, ret)
                    cv2.imshow('img', image)
                    cv2.waitKey(500)
        self.image_size = gray.shape[::-1]
        cv2.destroyAllWindows()

    def _calculate_calibration(self):
        _, mtx, dist, _, _ = cv2.calibrateCamera(self.obj_points, self.image_points, self.image_size, None, None)
        if self.show_progress:
            print('Matrix:', mtx)
            print('Dist. coef:', dist)
        return mtx, dist

    def _calculate_camera_fov(self, mtx):
        fov_x, fov_y, _, _, _ = cv2.calibrationMatrixValues(mtx, self.image_size, 1, 1)
        if self.show_progress:
            print('FOV_x:', fov_x)
            print('FOV_y:', fov_y)
        return fov_x, fov_y

    def __call__(self, in_folder, save_file, show_detections=False, *args, **kwargs):
        self._detect_checkerboard(in_folder, show_detections)
        mtx, dist = self._calculate_calibration()
        fov_x, fov_y = self._calculate_camera_fov(mtx)
        np.savez(save_file, mtx=mtx, dist=dist, fov_x=fov_x, fov_y=fov_y)


class Undistort:
    def __init__(self, calibration_file):
        self.mtx, self.dist = self._read_calibration(calibration_file)

    @staticmethod
    def _read_calibration(file):
        np_file = np.load(file)
        mtx = np_file['mtx']
        dist = np_file['dist']
        return mtx, dist

    def __call__(self, image, crop=False, *args, **kwargs):
        height, width = image.shape[:2]
        size = (width, height)
        new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, size, 1, size)
        dst = cv2.undistort(image, self.mtx, self.dist, None, new_camera_mtx)
        if crop:
            x, y, w, h = roi
            dst = dst[y:y + h, x:x + w]
        return dst



