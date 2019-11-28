import json
import numpy as np


class Annotation:
    def __init__(self, text):
        self.text = text
        self.nodes = []


class Annotations:
    def __init__(self, drone_log, fov):
        self.drone_log = drone_log
        self.fov = fov
        self.parents = []

    def add_parent(self, name):
        parent = Annotation(name)
        self.parents.append(parent)

    def add_node(self, text, parent_name):
        p = self.get_parent(parent_name)
        node = Annotation(text)
        p.nodes.append(node)

    def get_parent(self, name):
        for p in self.parents:
            if p.text == name:
                return p
        return None

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
        self.parents = []
        json_dict = json.loads(fabric_json)
        objects = json_dict.get('objects')
        if objects:
            for obj in objects:
                if obj.get('type') == 'FrameLine':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    length = self._get_length(obj)
                    text = f'Line; Frame: {frame}, Length: {length:.2f}m'
                elif obj.get('type') == 'FramePoint':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    text = f'Point; Frame: {frame}'
                else:
                    continue
                parent = self.get_parent(name)
                if not parent:
                    self.add_parent(name)
                self.add_node(text, name)

    def to_json(self):
        json_obj = []
        for p in self.parents:
            node_list = []
            for node in p.nodes:
                node_dict = {'text': node.text}
                node_list.append(node_dict)
            p_dict = {'text': p.text, 'nodes': node_list}
            json_obj.append(p_dict)
        return json_obj
