from __future__ import annotations

import csv
import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np

from dvm.app_config import Drone, Project, Video
from dvm.drone.drone_log_data import drone_log
from dvm.drone.fov import fov

logger = logging.getLogger("app." + __name__)


def save_annotations_csv(annotations: list[list[Any] | None], filename: Path) -> None:
    logger.debug(f"Saving annotations in {filename}")
    with filename.open("w") as fp:
        csv_writer = csv.writer(fp, delimiter=",")
        header = (
            "name",
            "time",
            "frame",
            "height",
            "yaw",
            "pitch",
            "roll",
            "length",
            "lat",
            "lon",
            "east",
            "north",
            "zone number",
            "zone letter",
            "image_x",
            "image_y",
            "start_east",
            "start_north",
            "end_east",
            "end_north",
            "heading",
            "video",
            "project",
            "pro. version",
        )
        csv_writer.writerow(header)
        for annotation in annotations:
            if annotation:
                csv_writer.writerow(annotation)


def get_all_annotations(project: Project, pro_version: str, video: Video | None = None) -> list[list[Any] | None]:
    logger.debug("Getting all annotations")
    annotations = []
    drone = Drone.query.get_or_404(project.drone_id)
    fov.set_camera_params(*drone.calibration)
    drone_log.get_log_data(Path(project.log_file))
    videos = [video] if video else list(project.videos)
    for video in videos:
        try:
            json_data = json.loads(video.json_data)
            objects = json_data["objects"]
            drone_log.set_video_data(
                video.duration,
                video.frames,
                (video.width, video.height),
                (video.latitude, video.longitude),
            )
            fov.set_image_size(*drone_log.video_size)
            drone_log.match_log_and_video()
            if objects:
                for obj in objects:
                    if obj["type"] == "FrameLine" or obj["type"] == "FramePoint":
                        annotation = get_frame_obj_data(obj)
                        if annotation is not None:
                            annotation.extend([video.name, project.name, pro_version])
                    else:
                        logger.debug(f"Unknown annotation found of type: {obj['type']}")
                        annotation = None
                    annotations.append(annotation)
        except Exception as e:
            logger.debug("Encountered an error while exporting data")
            logger.debug(e)
    return annotations


def get_frame_obj_data(obj: dict[str, Any]) -> list[Any] | None:
    name = obj["name"]
    frame_number = obj["frame"]
    log_data = drone_log.get_log_data_from_frame(frame_number)
    if obj["type"] == "FrameLine":
        x1 = obj["x1"]
        x2 = obj["x2"]
        y1 = obj["y1"]
        y2 = obj["y2"]
        xoffset = obj["left"] + obj["width"] / 2
        yoffset = obj["top"] + obj["height"] / 2
        image_point1 = (x1 + xoffset, y1 + yoffset)
        image_point2 = (x2 + xoffset, y2 + yoffset)
        image_point = (
            (image_point1[0] + image_point2[0]) / 2,
            (image_point1[1] + image_point2[1]) / 2,
        )
        wp1, zone = fov.get_world_point(image_point1, *log_data[1:], return_zone=True)
        wp2 = fov.get_world_point(image_point2, *log_data[1:])
        wp = np.array([(wp1[0] + wp2[0]) / 2, (wp1[1] + wp2[1]) / 2])
        length = np.sqrt((wp1[0] - wp2[0]) ** 2 + (wp1[1] - wp2[1]) ** 2)
        dx = wp2[0] - wp1[0]
        dy = wp2[1] - wp1[1]
        heading = 180 / math.pi * math.atan2(dx, dy)
    elif obj["type"] == "FramePoint":
        image_point = (obj["left"], obj["top"])
        wp, zone = fov.get_world_point(image_point, *log_data[1:], return_zone=True)
        length = "NA"
        heading = "NA"  # type: ignore[assignment]
        wp1 = ["NA", "NA"]
        wp2 = ["NA", "NA"]
    else:
        return None
    pos = fov.convert_utm(wp[0], wp[1], zone)
    yaw = log_data[2][0] * 180 / np.pi
    pitch = log_data[2][1] * 180 / np.pi
    roll = log_data[2][2] * 180 / np.pi
    annotation = [
        name,
        log_data[0],
        frame_number,
        log_data[1],
        yaw,
        pitch,
        roll,
        length,
        pos[0],
        pos[1],
        wp[0],
        wp[1],
        zone[0],
        zone[1],
        image_point[0],
        image_point[1],
        wp1[0],
        wp1[1],
        wp2[0],
        wp2[1],
        heading,
    ]
    return annotation
