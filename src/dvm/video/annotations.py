from __future__ import annotations

import json
import logging

import numpy as np

from dvm.drone.drone_log_data import DroneLog
from dvm.drone.fov import Fov

logger = logging.getLogger("app." + __name__)


class Annotations:
    def __init__(self, drone_log: DroneLog, fov: Fov) -> None:
        logger.debug(f"Creating Annotations instance: {self}")
        self.drone_log = drone_log
        self.fov = fov
        self.tree_json: list[dict[str, str]] = []

    def _get_length(self, obj: dict[str, int]) -> float:
        log_data = self.drone_log.get_log_data_from_frame(obj["frame"])
        x1 = obj["x1"]
        x2 = obj["x2"]
        y1 = obj["y1"]
        y2 = obj["y2"]
        xoffset = obj["left"] + obj["width"] / 2
        yoffset = obj["top"] + obj["height"] / 2
        image_point1 = (x1 + xoffset, y1 + yoffset)
        image_point2 = (x2 + xoffset, y2 + yoffset)
        wp1 = self.fov.get_world_point(image_point1, *log_data[1:])
        wp2 = self.fov.get_world_point(image_point2, *log_data[1:])
        length = float(np.sqrt((wp1[0] - wp2[0]) ** 2 + (wp1[1] - wp2[1]) ** 2))  # type: ignore[operator]
        return length

    def from_fabric_json(self, fabric_json: str) -> None:
        parents = set()
        idx = 0
        self.tree_json = []
        json_dict = json.loads(fabric_json)
        objects = json_dict.get("objects")
        if objects:
            for obj in objects:
                if obj.get("type") == "FrameLine":
                    name = obj.get("name")
                    frame = obj.get("frame")
                    length = self._get_length(obj)
                    text = f"<span>Line; Frame: {frame}, Length: {length:.2f}m</span>"
                elif obj.get("type") == "FramePoint":
                    name = obj.get("name")
                    frame = obj.get("frame")
                    text = f"Point; Frame: {frame}"
                else:
                    continue
                if name not in parents:
                    parent = {
                        "id": name,
                        "parent": "#",
                        "text": name,
                        "icon": "far fa-folder",
                    }
                    self.tree_json.append(parent)
                    parents.add(name)
                node = {"id": idx, "parent": name, "text": text, "icon": "-"}
                idx += 1
                self.tree_json.append(node)
        if not self.tree_json:
            self.tree_json.append(
                {
                    "id": "Doodles",
                    "parent": "#",
                    "text": "Doodles",
                    "icon": "far fa-folder",
                }
            )
