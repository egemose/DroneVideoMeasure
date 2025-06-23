from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from dvm.app_config import AppConfig
from dvm.calibration.corner_detector import ChessBoardCornerDetector

logger = logging.getLogger("app." + __name__)


class CalibrateCamera:
    def __init__(self) -> None:
        self.min_percentage_coverage = 15
        self.detector = ChessBoardCornerDetector()

    def detect_calibration_pattern_in_image(
        self, img: np.ndarray, filename: Path
    ) -> tuple[np.ndarray, np.ndarray, int]:
        corners, coverage, _ = self.detector.detect_chess_board_corners(
            img,
            debug=True,
            path_to_image=Path(filename),
            path_to_output_folder=AppConfig.data_dir.joinpath("calibrationtemp"),
        )
        obj_points = []
        img_points = []
        for key, val in corners.items():
            for inner_key, inner_val in val.items():
                obj_points.append(np.array([key, inner_key, 0]))
                img_points.append(inner_val)
        return (
            np.array(obj_points, dtype=np.float32),
            np.array(img_points, dtype=np.float32),
            coverage,
        )

    def calibrate_camera_from_images(
        self, image_files: list[Path]
    ) -> tuple[np.ndarray, np.ndarray, tuple[int, int], int] | None:
        obj_points_list = []
        img_points_list = []
        for image_file in image_files:
            img = cv2.imread(str(image_file))
            image_size = (img.shape[1], img.shape[0])
            try:
                obj_points, img_points, coverage = self.detect_calibration_pattern_in_image(img, filename=image_file)
                if coverage > self.min_percentage_coverage:
                    obj_points_list.append(obj_points)
                    img_points_list.append(img_points)
                else:
                    logger.debug(
                        f"{image_file} only has {coverage}% coverage minimum set to {self.min_percentage_coverage}"
                    )
            except Exception as e:
                print("Something failed in calibrate_camera_from_images")
                print(e)
        if obj_points_list:
            n_images_used_for_calibration = len(obj_points_list)
            logger.debug(f"Using {n_images_used_for_calibration} images to calibrate")
            _, mtx, dist, _, _ = cv2.calibrateCamera(obj_points_list, img_points_list, image_size, None, None)
            return mtx, dist, image_size, n_images_used_for_calibration
        else:
            logger.debug("No usable images found")
            return None

    def calibrate_camera_from_video(
        self, video_files: list[Path]
    ) -> tuple[np.ndarray, np.ndarray, tuple[int, int], int] | None:
        obj_points_list = []
        img_points_list = []
        for video_file in video_files:
            cap = cv2.VideoCapture(str(video_file))
            num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            num_images = 30
            logger.debug(f"Number of frames in video: {num_frames}")
            logger.debug(f"Number of images to extract: {num_images}")
            count = 0
            while cap.isOpened():
                # Set next frame to read
                logger.debug(f"Next frame to extract is: {count}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, count)

                # Read frame
                ret_val, frame = cap.read()
                if ret_val:
                    logger.debug(f"Examining frame {count} for calibration pattern coverage")
                    image_size = (frame.shape[1], frame.shape[0])
                    obj_points, img_points, coverage = self.detect_calibration_pattern_in_image(
                        frame, filename=Path(f"frame_from_video_{count}.png")
                    )
                    if coverage > self.min_percentage_coverage:
                        logger.debug(f"Calibration pattern coverage is fine ({coverage})")
                        obj_points_list.append(obj_points)
                        img_points_list.append(img_points)
                    else:
                        logger.debug(f"Calibration pattern coverage too low in image ({coverage})")
                        num_images = num_images + 1 if num_images < 30 else 30

                # Calculate next frame to extract
                count += int(num_frames / num_images)
                if count > num_frames:
                    break
            cap.release()
        if obj_points_list:
            n_images_used_for_calibration = len(obj_points_list)
            logger.debug(f"Using {n_images_used_for_calibration} images from video to calibrate")
            _, mtx, dist, _, _ = cv2.calibrateCamera(obj_points_list, img_points_list, image_size, None, None)
            return mtx, dist, image_size, n_images_used_for_calibration
        else:
            logger.debug("No usable images found in the video")
            return None

    @staticmethod
    def calculate_camera_fov(mtx: np.ndarray, image_size: tuple[int, int]) -> tuple[float, float]:
        fov_x, fov_y, _, _, _ = cv2.calibrationMatrixValues(mtx, image_size, 1, 1)
        return fov_x, fov_y

    def __call__(
        self, in_folder: Path, *args: tuple[Any, ...], **kwargs: dict[str, Any]
    ) -> tuple[np.ndarray, np.ndarray, float, float, int] | int | None:
        logger.debug("Calibrating camera")
        image_files: list[Path] = []
        for file_format in [
            "*.jpg",
            "*.jpeg",
            "*.jpe",
            "*.bmp",
            "*.dib",
            "*.png",
            "*.tiff",
            "*.tif",
        ]:
            image_files.extend(in_folder.glob(file_format, case_sensitive=False))
        video_files: list[Path] = []
        for file_format in [
            "*.mp4",
            "*.m4a",
            "*.m4v",
            "*.f4v",
            "*.f4a",
            "*.m4b",
            "*.m4r",
            "*.f4b",
            "*.mov",
            "*.wmv",
            "*.wma",
            "*.webm",
        ]:
            video_files.extend(in_folder.glob(file_format, case_sensitive=False))
        if image_files:
            res = self.calibrate_camera_from_images(image_files)
        elif video_files:
            res = self.calibrate_camera_from_video(video_files)
        else:
            return None
        if res is None:
            return -1
        else:
            mtx, dist, image_size, n_images = res
            fov_x, fov_y = self.calculate_camera_fov(mtx, image_size)
            return mtx, dist, fov_x, fov_y, n_images
