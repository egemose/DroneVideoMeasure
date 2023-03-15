import csv
import os
import re
import utm
from datetime import datetime, timedelta
import ffmpeg
import numpy as np
from app_config import data_dir
import logging

logger = logging.getLogger('app.' + __name__)


class DroneLog:
    def __init__(self):
        logger.debug(f'Creating DroneLog instance {self}')
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
        logger.debug(f'Getting log data')
        yaw = [x[0] * 180 / np.pi for x in self.rotation]
        pitch = [x[1] * 180 / np.pi for x in self.rotation]
        roll = [x[2] * 180 / np.pi for x in self.rotation]
        return self.time_stamp, self.height, yaw, pitch, roll, self.is_video

    @staticmethod
    def test_log(log):
        res = DroneLog.test_log_txt_to_log_csv_file(log)
        if res is True:
            return True
        res = DroneLog.test_log_air_data(log)
        return res

    @staticmethod
    def test_log_air_data(log):
        indexes = ['time(millisecond)', 'datetime(utc)', 'latitude', 'longitude', 'height_above_takeoff(meters)', 'altitude_above_seaLevel(meters)', 'height_sonar(meters)', 'isPhoto', 'isVideo', 'gimbal_heading(degrees)', 'gimbal_pitch(degrees)', 'gimbal_roll(degrees)', 'altitude(meters)']
        #remove_null_bytes(log)
        logger.debug(f'Opening log "{log}" to test - assuming it contains data from airdata.com ')
        with open(log, encoding='iso8859_10') as csv_file:
            reader = csv.DictReader(csv_file)
            row = next(reader)
            for idx in indexes:
                if idx not in row.keys():
                    logger.debug(f'Could not locate the column { idx } in the uploaded logfile')
                    return False
            logger.debug(f'Found all expected columns in the log file (airdata.com format)')
            return True

    @staticmethod
    def test_log_txt_to_log_csv_file(log):
        indexes = ['CUSTOM.updateTime', 'GIMBAL.yaw', 'GIMBAL.pitch', 'GIMBAL.roll', 'OSD.height [m]', 'CUSTOM.isVideo', 'OSD.latitude', 'OSD.longitude']
        remove_null_bytes(log)
        logger.debug(f'Opening log "{log}" to test - assuming it contains data from TXTlogToCSVtool.exe')
        with open(log, encoding='iso8859_10') as csv_file:
            reader = csv.DictReader(csv_file)
            row = next(reader)
            for idx in indexes:
                if idx not in row.keys():
                    logger.debug(f'Could not locate the column { idx } in the uploaded logfile')
                    return False
            logger.debug(f'Found all expected columns in the log file (TXTlogToCSVtool.exe)')
            return True

    def get_log_data(self, log):
        try: 
            self.get_log_data_txt_to_log_csv_file(log)
        except KeyError as e:
            logger.debug('Encoutered issue in get_log_data - KeyError')
            logger.debug(e)
        self.get_log_data_air_data_com(log)


    def get_log_data_air_data_com(self, log):
        logger.debug(f'Getting log data for {log}')
        self.time_stamp = []
        self.height = []
        self.rotation = []
        self.pos = []
        self.is_video = []
        indexes = ['time(millisecond)'
, 'datetime(utc)', 'latitude', 'longitude', 'height_above_takeoff(meters)', 'altitude_above_seaLevel(meters)', 'height_sonar(meters)', 'isPhoto', 'isVideo', 'gimbal_heading(degrees)', 'gimbal_pitch(degrees)', 'gimbal_roll(degrees)', 'altitude(meters)']
        time_idx = 'datetime(utc)'
        yaw_idx = 'gimbal_heading(degrees)'
        pitch_idx = 'gimbal_pitch(degrees)'
        roll_idx = 'gimbal_roll(degrees)'
        height_idx = 'height_sonar(meters)'
        is_video_idx = 'isVideo'
        latitude_idx = 'latitude'
        longitude_idx = 'longitude'
        remove_null_bytes(log)
        number_of_parsed_lines = 0
        with open(log, encoding='iso8859_10') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row[time_idx]:
                    try:
                        # TODO: take into account the "time(milisecond)" column when computing the timestamp.
                        self.time_stamp.append(datetime.strptime(row[time_idx], '%Y-%m-%d %H:%M:%S.%f'))
                    except ValueError:
                        # TODO: take into account the "time(milisecond)" column when computing the timestamp.
                        self.time_stamp.append(datetime.strptime(row[time_idx], '%Y-%m-%d %H:%M:%S'))
                    try:
                        self.height.append(float(row[height_idx]))
                        yaw = float(row[yaw_idx]) * np.pi / 180
                        pitch = float(row[pitch_idx]) * np.pi / 180
                        roll = float(row[roll_idx]) * np.pi / 180
                        self.rotation.append((yaw, pitch, roll))
                        latitude = float(row[latitude_idx])
                        longitude = float(row[longitude_idx])
                        self.pos.append((latitude, longitude))
                        self.is_video.append(True if row[is_video_idx]=="1" else False)
                    except ValueError as VE:
                        logger.debug(f'Row skipped because of value error ({ VE }).')
                        continue
                    number_of_parsed_lines += 1
        logger.debug(f'Number of parsed lines: { number_of_parsed_lines }')
            

    def get_log_data_txt_to_log_csv_file(self, log):
        logger.debug(f'Getting log data for {log}')
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
        remove_null_bytes(log)
        number_of_parsed_lines = 0
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
                    except ValueError as VE:
                        logger.debug(f'Row skipped because of value error ({ VE }).')
                        continue
                    number_of_parsed_lines += 1
        logger.debug(f'Number of parsed lines: { number_of_parsed_lines }')

    def get_video_data(self, project, video_file):
        logger.debug(f'Reading video data for video {video_file} in {project}')
        file = os.path.join(data_dir, 'projects', project, video_file)
        ffprobe_res = ffmpeg.probe(file, cmd='ffprobe')
        self.video_duration = float(ffprobe_res['format']['duration'])
        self.video_nb_frames = int(ffprobe_res['streams'][0]['nb_frames'])
        self.video_size = (int(ffprobe_res['streams'][0]['width']), int(ffprobe_res['streams'][0]['height']))
        location_string = ffprobe_res['format']['tags']['location']
        match = re.match(r'([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)', location_string)
        self.video_pos = None
        if match:
            self.video_pos = (float(match.group(1)), float(match.group(2)))

    def get_video_data_from_data_file(self, project, video_file):
        logger.debug(f'Reading video data from data file for video {video_file} from {project}')
        video_data_file = os.path.join(data_dir, 'projects', project, video_file + '_data.txt')
        with open(video_data_file, 'r', newline='') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                self.video_duration = float(row['duration'])
                self.video_nb_frames = int(row['nb_frames'])
                self.video_size = (int(row['width']), int(row['height']))
                if row['lat']:
                    self.video_pos = (float(row['lat']), float(row['long']))
                else:
                    self.video_pos = None

    def set_video_data(self, duration, frames, size, pos):
        self.video_duration = duration
        self.video_nb_frames = frames
        self.video_size = size
        self.video_pos = pos

    def match_log_and_video(self):
        logger.debug(f'Matching video and log file')
        message = None
        video_ranges = list(get_video_ranges(self.is_video, self.time_stamp))
        if self.video_pos is not None and self.video_pos[0] is not None:
            video_utm_pos = utm.from_latlon(*self.video_pos)
            start_utm_pos = [utm.from_latlon(*self.pos[self.time_stamp.index(y[0])]) for y in video_ranges]
            minimum = min([(abs(video_utm_pos[0] - x[0]) + abs(video_utm_pos[1] - x[1]), y[0]) for x, y in zip(start_utm_pos, video_ranges)], key=lambda z: z[0])
            if minimum[0] > 1:
                message = f'Warning: Video position and Drone Log position differs by {minimum[0]:.2f} meter.'
        else:
            minimum = min([(abs((x[1] - x[0]).total_seconds() - self.video_duration), x[0]) for x in video_ranges], key=lambda y: y[0])
            if minimum[0] > 5:
                message = f'Warning: Video duration ({self.video_duration:.2f}) and Drone Log video duration differs by {minimum[0]:.2f} seconds.'
        logger.debug(f'Matching message: {message}')
        self.video_start_time = minimum[1]
        return minimum[1], message

    def get_log_data_from_frame(self, frame):
        logger.debug(f'Getting log data for frame {frame}')
        delta_time = timedelta(seconds=frame / self.video_nb_frames * self.video_duration)
        time = self.video_start_time + delta_time
        idx = self.get_time_idx(time)
        return self.time_stamp[idx], self.height[idx], self.rotation[idx], self.pos[idx]

    def get_time_idx(self, time):
        minimum = min([(abs((x - time).total_seconds()), idx) for idx, x in enumerate(self.time_stamp)], key=lambda y: y[0])
        return minimum[1]


def remove_null_bytes(log):
    logger.debug(f'Removing null bytes from log: {log}')
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
