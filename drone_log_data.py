import csv
import os
import re
from datetime import datetime, timedelta
import ffmpeg
import numpy as np
from help_functions import base_dir


class DroneLog:
    def __init__(self):
        self.video_duration = None
        self.video_nb_frames = None
        self.video_size = None
        self.video_pos = None
        self.video_start_time = None
        self.time_stamp = None
        self.height = None
        self.rotation = None
        self.pos = None
        self.is_video = None

    def log_data(self):
        yaw = [x[0] * 180 / np.pi for x in self.rotation]
        pitch = [x[1] * 180 / np.pi for x in self.rotation]
        roll = [x[2] * 180 / np.pi for x in self.rotation]
        return self.time_stamp, self.height, yaw, pitch, roll, self.is_video

    @staticmethod
    def test_log(project):
        indexes = ['CUSTOM.updateTime', 'GIMBAL.yaw', 'GIMBAL.pitch', 'GIMBAL.roll', 'OSD.height [m]', 'CUSTOM.isVideo', 'OSD.latitude', 'OSD.longitude']
        log = os.path.join(base_dir, 'projects', project, 'drone_log.csv')
        remove_null_bytes(log)
        with open(log, encoding='iso8859_10') as csv_file:
            reader = csv.DictReader(csv_file)
            row = next(reader)
            for idx in indexes:
                if idx not in row.keys():
                    return False
            return True

    def get_log_data(self, project):
        self.time_stamp = []
        self.height = []
        self.rotation = []
        self.pos = []
        self.is_video = []
        time_idx = 'CUSTOM.updateTime'
        yaw_idx = 'GIMBAL.yaw'
        pitch_idx = 'GIMBAL.pitch'
        roll_idx = 'GIMBAL.roll'
        height_idx = 'OSD.height [m]'
        is_video_idx = 'CUSTOM.isVideo'
        latitude_idx = 'OSD.latitude'
        longitude_idx = 'OSD.longitude'
        log = os.path.join(base_dir, 'projects', project, 'drone_log.csv')
        remove_null_bytes(log)
        with open(log, encoding='iso8859_10') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row[time_idx]:
                    try:
                        self.time_stamp.append(datetime.strptime(row[time_idx], '%Y/%m/%d %H:%M:%S.%f'))
                    except ValueError:
                        self.time_stamp.append(datetime.strptime(row[time_idx], '%Y/%m/%d %H:%M:%S'))
                    try:
                        self.height.append(float(row[height_idx]))
                        yaw = float(row[yaw_idx]) * np.pi / 180
                        pitch = float(row[pitch_idx]) * np.pi / 180
                        roll = float(row[roll_idx]) * np.pi / 180
                        self.rotation.append((yaw, pitch, roll))
                        latitude = float(row[latitude_idx])
                        longitude = float(row[longitude_idx])
                        self.pos.append((latitude, longitude))
                        self.is_video.append(True if row[is_video_idx] else False)
                    except ValueError:
                        continue

    def get_video_data(self, project, video_file):
        file = os.path.join(base_dir, 'projects', project, video_file)
        ffprobe_res = ffmpeg.probe(file, cmd='ffprobe')
        self.video_duration = float(ffprobe_res['format']['duration'])
        self.video_nb_frames = int(ffprobe_res['streams'][0]['nb_frames'])
        self.video_size = (int(ffprobe_res['streams'][0]['width']), int(ffprobe_res['streams'][0]['height']))
        location_string = ffprobe_res['format']['tags']['location']
        match = re.match(r'([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)', location_string)
        self.video_pos = None
        if match:
            self.video_pos = (float(match.group(1)), float(match.group(2)))

    def match_log_and_video(self):
        message = None
        video_ranges = list(get_video_ranges(self.is_video, self.time_stamp))
        if self.video_pos is not None:
            start_pos = [self.pos[self.time_stamp.index(y[0])] for y in video_ranges]
            minimum = min([(abs(self.video_pos[0] - x[0]) + abs(self.video_pos[1] - x[1]), y[0]) for x, y in zip(start_pos, video_ranges)], key=lambda z: z[0])
            if minimum[0] > 0.00001:
                message = 'Warning: Video position and Drone Log position differs by more then 1 meter.'
            if minimum[0] > 0.0001:
                message = 'Warning: Video position and Drone Log position differs by more then 10 meter.'
            if minimum[0] > 0.001:
                message = 'Warning: Video position and Drone Log position differs by more then 100 meter.'
        else:
            minimum = min([(abs((x[1] - x[0]).total_seconds() - self.video_duration), x[0]) for x in video_ranges], key=lambda y: y[0])
            if minimum[0] > 5:
                message = f'Warning: Video duration and Drone Log video duration differs by {minimum[0]} seconds.'
        self.video_start_time = minimum[1]
        return minimum[1], message

    def get_log_data_from_frame(self, frame):
        delta_time = timedelta(seconds=frame / self.video_nb_frames * self.video_duration)
        time = self.video_start_time + delta_time
        idx = self.get_time_idx(time)
        return self.time_stamp[idx], self.height[idx], self.rotation[idx], self.pos[idx]

    def get_time_idx(self, time):
        minimum = min([(abs((x - time).total_seconds()), idx) for idx, x in enumerate(self.time_stamp)], key=lambda y: y[0])
        return minimum[1]


def remove_null_bytes(log):
    with open(log, 'rb') as fi:
        data = fi.read()
    with open(log, 'wb') as fo:
        fo.write(data.replace(b'\x00', b''))


def get_video_ranges(is_video, time_stamp):
    last_state = False
    video_begin = None
    t = 0
    for k, t in zip(is_video, time_stamp):
        if k and not last_state:
            video_begin = t
        if not k and last_state:
            yield video_begin, t
        last_state = k
    if last_state:
        yield video_begin, t


drone_log = DroneLog()
