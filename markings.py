import json


class MarkingView:
    def __init__(self):
        self.data = {}
        self.add_name('Doodles')

    @classmethod
    def from_fabric_json(cls, fabric_json):
        marking = cls()
        marking._parse_fabric_json(fabric_json)
        return marking

    def _parse_fabric_json(self, fabric_json):
        json_dict = json.loads(fabric_json)
        objs = json_dict.get('objects')
        if objs:
            for obj in objs:
                if obj.get('type') == 'FrameLine':
                    # todo get length
                    name = obj.get('name')
                    frame = obj.get('frame')
                    length = 10
                    string = f'Frame: {frame}, Length: {length}m'
                    self.add_marking(name, string)

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

