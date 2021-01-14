import json
import numpy as np
import logging

logger = logging.getLogger('app.' + __name__)


class Annotations:
    def __init__(self, drone_log, fov):
        logger.debug(f'Creating Annotations instance: {self}')
        self.drone_log = drone_log
        self.fov = fov
        self.tree_json = []

    def _get_length(self, obj):
        log_data = self.drone_log.get_log_data_from_frame(obj.get('frame'))
        x1 = obj.get('x1')
        x2 = obj.get('x2')
        y1 = obj.get('y1')
        y2 = obj.get('y2')
        direction = (x1 < 0 and y1 < 0) or (x2 < 0 and y2 < 0)
        if direction:
            image_point1 = (obj.get('left'), obj.get('top'))
            image_point2 = (obj.get('left') + obj.get('width'), obj.get('top') + obj.get('height'))
        else:
            image_point1 = (obj.get('left') + obj.get('width'), obj.get('top'))
            image_point2 = (obj.get('left'), obj.get('top') + obj.get('height'))
        wp1 = self.fov.get_world_point(image_point1, *log_data[1:])
        wp2 = self.fov.get_world_point(image_point2, *log_data[1:])
        length = np.sqrt((wp1[0] - wp2[0]) ** 2 + (wp1[1] - wp2[1]) ** 2)
        return length

    def from_fabric_json(self, fabric_json):
        parents = set()
        idx = 0
        self.tree_json = []
        json_dict = json.loads(fabric_json)
        objects = json_dict.get('objects')
        if objects:
            for obj in objects:
                if obj.get('type') == 'FrameLine':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    length = self._get_length(obj)
                    text = f'<span>Line; Frame: {frame}, Length: {length:.2f}m</span>'
                elif obj.get('type') == 'FramePoint':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    text = f'Point; Frame: {frame}'
                else:
                    continue
                if name not in parents:
                    parent = {'id': name, 'parent': '#', 'text': name}
                    self.tree_json.append(parent)
                    parents.add(name)
                node = {'id': idx, 'parent': name, 'text': text}
                idx += 1
                self.tree_json.append(node)
        if not self.tree_json:
            self.tree_json.append({'id': 'Doodles', 'parent': '#', 'text': 'Doodles'})
