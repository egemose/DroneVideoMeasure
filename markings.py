import json
import numpy as np


class MarkingView:
    def __init__(self, drone_log, fov):
        self.data = {}
        self.add_name('Doodles')
        self.drone_log = drone_log
        self.fov = fov

    @classmethod
    def from_fabric_json(cls, fabric_json, drone_log, fov):
        marking = cls(drone_log, fov)
        marking._parse_fabric_json(fabric_json)
        return marking

    def _parse_fabric_json(self, fabric_json):
        json_dict = json.loads(fabric_json)
        objs = json_dict.get('objects')
        if objs:
            for obj in objs:
                if obj.get('type') == 'FrameLine':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    length = self._get_length(obj)
                    string = f'Line; Frame: {frame}, Length: {length:.2f}m'
                    self.add_marking(name, string)
                if obj.get('type') == 'FramePoint':
                    name = obj.get('name')
                    frame = obj.get('frame')
                    string = f'Point; Frame: {frame}'
                    self.add_marking(name, string)

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

    def add_marking(self, name, text):
        marking = {'text': text}
        name_dict = self.data.get(name)
        if not name_dict:
            name_dict = {'text': name, 'nodes': []}
            self.data.update({name: name_dict})
        name_dict.get('nodes').append(marking)

    def add_name(self, name):
        name_dict = {'text': name, 'nodes': []}
        self.data.update({name: name_dict})

    def get_data(self):
        data = []
        for v in self.data.values():
            data.append(v)
        return data

