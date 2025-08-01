from __future__ import annotations

import csv
import logging
import re
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path

import ffmpeg
import numpy as np
import utm

from dvm.app_config import AppConfig

logger = logging.getLogger("app." + __name__)


class DroneLog:
    def __init__(self) -> None:
        logger.debug(f"Creating DroneLog instance {self}")
        self.video_duration: float
        self.video_nb_frames: int
        self.video_size: tuple[int, int]
        self.video_pos: tuple[float, float] | None
        self.video_start_time: datetime | None = None
        self.time_stamp: list[datetime]
        self.height: list[float]
        self.rotation: list[tuple[float, float, float]]
        self.pos: list[tuple[float, float]]
        self.is_video: list[bool]
        self.takeoff_altitude = 0.0

    def log_data(self) -> tuple[list[datetime], list[float], list[float], list[float], list[float], list[bool]]:
        logger.debug("Getting log data")
        yaw = [x[0] * 180 / np.pi for x in self.rotation]
        pitch = [x[1] * 180 / np.pi for x in self.rotation]
        roll = [x[2] * 180 / np.pi for x in self.rotation]
        return self.time_stamp, self.height, yaw, pitch, roll, self.is_video

    @staticmethod
    def test_log(log: Path) -> bool:
        res = DroneLog.test_log_txt_to_log_csv_file(log)
        if res is True:
            return True
        res = DroneLog.test_log_air_data(log)
        return res

    @staticmethod
    def test_log_air_data(log: Path) -> bool:
        indexes = [
            "time(millisecond)",
            "datetime(utc)",
            "latitude",
            "longitude",
            "height_above_takeoff(meters)",
            "altitude_above_seaLevel(meters)",
            "height_sonar(meters)",
            "isPhoto",
            "isVideo",
            "gimbal_heading(degrees)",
            "gimbal_pitch(degrees)",
            "gimbal_roll(degrees)",
            "altitude(meters)",
        ]
        # remove_null_bytes(log)
        logger.debug(f'Opening log "{log}" to test - assuming it contains data from airdata.com ')
        with log.open(encoding="iso8859_10") as csv_file:
            reader = csv.DictReader(csv_file)
            row = next(reader)
            for idx in indexes:
                if idx not in row:
                    logger.debug(f"Could not locate the column {idx} in the uploaded logfile")
                    return False
            logger.debug("Found all expected columns in the log file (airdata.com format)")
            return True

    @staticmethod
    def test_log_txt_to_log_csv_file(log: Path) -> bool:
        indexes = [
            "CUSTOM.updateTime",
            "GIMBAL.yaw",
            "GIMBAL.pitch",
            "GIMBAL.roll",
            "OSD.height [m]",
            "CUSTOM.isVideo",
            "OSD.latitude",
            "OSD.longitude",
        ]
        remove_null_bytes(log)
        logger.debug(f'Opening log "{log}" to test - assuming it contains data from TXTlogToCSVtool.exe')
        with log.open(encoding="iso8859_10") as csv_file:
            reader = csv.DictReader(csv_file)
            row = next(reader)
            for idx in indexes:
                if idx not in row:
                    logger.debug(f"Could not locate the column {idx} in the uploaded logfile")
                    return False
            logger.debug("Found all expected columns in the log file (TXTlogToCSVtool.exe)")
            return True

    def get_log_data(self, log: Path) -> None:
        try:
            self.get_log_data_txt_to_log_csv_file(log)
            return
        except KeyError as e:
            logger.debug("Encountered issue in get_log_data - KeyError")
            logger.debug(e)
        except Exception as e:
            logger.debug("Encountered issue in get_log_data")
            logger.debug(e)
        # If the logfile format differs from the output from TXTlogToCSVtool.exe
        # try to handle it as a file from airdata.com
        self.get_log_data_air_data_com(log)

    def get_log_data_air_data_com(self, log: Path) -> None:
        logger.debug(f"Getting log data for {log}")
        self.time_stamp = []
        self.height = []
        self.rotation = []
        self.pos = []
        self.is_video = []
        time_idx = "datetime(utc)"
        time_milliseconds_idx = "time(millisecond)"
        yaw_idx = "gimbal_heading(degrees)"
        pitch_idx = "gimbal_pitch(degrees)"
        roll_idx = "gimbal_roll(degrees)"
        height_idx = "height_above_takeoff(meters)"
        is_video_idx = "isVideo"
        latitude_idx = "latitude"
        longitude_idx = "longitude"
        remove_null_bytes(log)
        number_of_parsed_lines = 0
        first_row = None
        with log.open(encoding="iso8859_10") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row[time_idx]:
                    if first_row is None:
                        first_row = row[time_idx]
                        date_time_first_row = datetime.strptime(row[time_idx], "%Y-%m-%d %H:%M:%S")
                    try:
                        self.time_stamp.append(
                            date_time_first_row + timedelta(milliseconds=float(row[time_milliseconds_idx]))
                        )
                        self.height.append(float(row[height_idx]))
                        yaw = float(row[yaw_idx]) * np.pi / 180
                        pitch = float(row[pitch_idx]) * np.pi / 180
                        roll = float(row[roll_idx]) * np.pi / 180
                        self.rotation.append((yaw, pitch, roll))
                        latitude = float(row[latitude_idx])
                        longitude = float(row[longitude_idx])
                        self.pos.append((latitude, longitude))
                        self.is_video.append(row[is_video_idx] == "1")
                    except ValueError as VE:
                        logger.debug(f"Row skipped because of value error ({VE}).")
                        continue
                    number_of_parsed_lines += 1
        logger.debug(f"Number of parsed lines: {number_of_parsed_lines}")

    def get_log_data_txt_to_log_csv_file(self, log: Path) -> None:
        logger.debug(f"Getting log data for {log}")
        self.time_stamp = []
        self.height = []
        self.rotation = []
        self.pos = []
        self.is_video = []
        time_idx = "CUSTOM.updateTime"
        yaw_idx = "GIMBAL.yaw"
        pitch_idx = "GIMBAL.pitch"
        roll_idx = "GIMBAL.roll"
        height_idx = "OSD.height [m]"
        is_video_idx = "CUSTOM.isVideo"
        latitude_idx = "OSD.latitude"
        longitude_idx = "OSD.longitude"
        remove_null_bytes(log)
        number_of_parsed_lines = 0
        with log.open(encoding="iso8859_10") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row[time_idx]:
                    try:
                        self.time_stamp.append(datetime.strptime(row[time_idx], "%Y/%m/%d %H:%M:%S.%f"))
                    except ValueError:
                        self.time_stamp.append(datetime.strptime(row[time_idx], "%Y/%m/%d %H:%M:%S"))
                    try:
                        self.height.append(float(row[height_idx]))
                        yaw = float(row[yaw_idx]) * np.pi / 180
                        pitch = float(row[pitch_idx]) * np.pi / 180
                        roll = float(row[roll_idx]) * np.pi / 180
                        self.rotation.append((yaw, pitch, roll))
                        latitude = float(row[latitude_idx])
                        longitude = float(row[longitude_idx])
                        self.pos.append((latitude, longitude))
                        self.is_video.append(bool(row[is_video_idx]))
                    except ValueError as VE:
                        logger.debug(f"Row skipped because of value error ({VE}).")
                        continue
                    number_of_parsed_lines += 1
        logger.debug(f"Number of parsed lines: {number_of_parsed_lines}")

    def get_video_data(self, project: str, video_file: str) -> None:
        logger.debug(f"Reading video data for video {video_file} in {project}")
        file = AppConfig.data_dir / "projects" / project / video_file
        ffprobe_res = ffmpeg.probe(file, cmd="ffprobe")
        self.video_duration = float(ffprobe_res["format"]["duration"])
        self.video_nb_frames = int(ffprobe_res["streams"][0]["nb_frames"])
        self.video_size = (
            int(ffprobe_res["streams"][0]["width"]),
            int(ffprobe_res["streams"][0]["height"]),
        )
        location_string = ffprobe_res["format"]["tags"]["location"]
        match = re.match(r"([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)", location_string)
        self.video_pos = None
        if match:
            self.video_pos = (float(match.group(1)), float(match.group(2)))

    def get_video_data_from_data_file(self, project: str, video_file: str) -> None:
        logger.debug(f"Reading video data from data file for video {video_file} from {project}")
        video_data_file = AppConfig.data_dir / "projects" / project / (video_file + "_data.txt")
        with video_data_file.open(newline="") as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                self.video_duration = float(row["duration"])
                self.video_nb_frames = int(row["nb_frames"])
                self.video_size = (int(row["width"]), int(row["height"]))
                if row["lat"]:
                    self.video_pos = (float(row["lat"]), float(row["long"]))
                else:
                    self.video_pos = None

    def set_video_data(self, duration: float, frames: int, size: tuple[int, int], pos: tuple[float, float]) -> None:
        self.video_duration = duration
        self.video_nb_frames = frames
        self.video_size = size
        self.video_pos = pos

    def match_log_and_video(self) -> tuple[datetime, str | None]:
        """
        If the video start time is not set for the video, this method
        makes a guess based on either location (if available)
        or duration.
        """
        logger.debug("Matching video and log file")
        if self.video_start_time is not None:
            logger.debug(f"self.video_start_time: {self.video_start_time}")
            return self.video_start_time, None
        video_ranges = list(get_video_ranges(self.is_video, self.time_stamp))
        if len(video_ranges) == 0:
            message = "Warning: No video recordings found in the logfile. You need to manually specify when the video recording started relative to the start of the logfile."
            minimum_log = min([(x, x) for x in self.time_stamp], key=lambda z: z[0])
            self.video_start_time = minimum_log[1]
        elif self.video_pos is not None and self.video_pos[0] is not None:
            minimum_pos = self.locate_best_match_based_on_location(video_ranges)
            self.video_start_time = minimum_pos[1]
            if minimum_pos[0] > 1:
                message = f"Warning: Video position and Drone Log position differs by {minimum_pos[0]:.2f} meter."
        else:
            minimum_duration = self.locate_best_match_based_on_duration(video_ranges)
            self.video_start_time = minimum_duration[1]
            if minimum_duration[0] > 5:
                message = f"Warning: Video duration ({self.video_duration:.2f}) and Drone Log video duration differs by {minimum_duration[0]:.2f} seconds."
        logger.debug(f"Matching message: {message}")
        return self.video_start_time, message

    def locate_best_match_based_on_location(
        self, video_ranges: list[tuple[datetime, datetime]]
    ) -> tuple[float, datetime]:
        video_utm_pos = utm.from_latlon(*self.video_pos)
        start_utm_pos = [utm.from_latlon(*self.pos[self.time_stamp.index(y[0])]) for y in video_ranges]
        minimum = min(
            [
                (abs(video_utm_pos[0] - x[0]) + abs(video_utm_pos[1] - x[1]), y[0])
                for x, y in zip(start_utm_pos, video_ranges, strict=False)
            ],
            key=lambda z: z[0],
        )
        return minimum

    def locate_best_match_based_on_duration(
        self, video_ranges: list[tuple[datetime, datetime]]
    ) -> tuple[float, datetime]:
        absolute_time_differences = [
            (abs((x[1] - x[0]).total_seconds() - self.video_duration), x[0]) for x in video_ranges
        ]
        minimum = min(absolute_time_differences, key=lambda y: y[0])
        return minimum

    def get_log_data_from_frame(
        self, frame: int
    ) -> tuple[datetime, float, tuple[float, float, float], tuple[float, float]]:
        logger.debug(f"Getting log data for frame {frame}")
        delta_time = timedelta(seconds=frame / self.video_nb_frames * self.video_duration)
        if self.video_start_time is not None:
            time = self.video_start_time + delta_time
        idx = self.get_time_idx(time)
        return (
            self.time_stamp[idx],
            self.height[idx] + self.takeoff_altitude,
            self.rotation[idx],
            self.pos[idx],
        )

    def get_time_idx(self, time: datetime) -> int:
        idx_and_absolute_time_difference = [
            (abs((x - time).total_seconds()), idx) for idx, x in enumerate(self.time_stamp)
        ]
        minimum = min(idx_and_absolute_time_difference, key=lambda y: y[0])
        return minimum[1]


def remove_null_bytes(log: Path) -> None:
    logger.debug(f"Removing null bytes from log: {log}")
    with log.open("rb") as fi:
        data = fi.read()
    with log.open("wb") as fo:
        fo.write(data.replace(b"\x00", b""))


def get_video_ranges(is_video: list[bool], time_stamp: list[datetime]) -> Generator[tuple[datetime, datetime]]:
    last_state = False
    for k, t in zip(is_video, time_stamp, strict=False):
        if k and not last_state:
            video_begin = t
        if not k and last_state:
            yield video_begin, t
        last_state = k
    if last_state:
        yield video_begin, t


drone_log = DroneLog()
