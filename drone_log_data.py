import csv
import os
import re
from collections import namedtuple
from datetime import datetime
import ffmpeg
import numpy as np
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.models import DatetimeTickFormatter, BoxAnnotation, Span, CustomJS
from bokeh.plotting import figure


log_data_tuple = namedtuple('log_data', ['time', 'height', 'rotation', 'position', 'is_video'])


def get_log_data(project):
    drone_log_data = []
    time_idx = 'CUSTOM.updateTime'
    yaw_idx = 'GIMBAL.yaw'
    pitch_idx = 'GIMBAL.pitch'
    roll_idx = 'GIMBAL.roll'
    height_idx = 'OSD.height [m]'
    is_video_idx = 'CUSTOM.isVideo'
    latitude_idx = 'OSD.latitude'
    longitude_idx = 'OSD.longitude'
    log = os.path.join('.', 'projects', project, 'drone_log.csv')
    remove_null_bytes(log)
    with open(log, encoding='iso8859_10') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row[time_idx]:
                try:
                    time_stamp = datetime.strptime(row[time_idx], '%Y/%m/%d %H:%M:%S.%f')
                except ValueError:
                    time_stamp = datetime.strptime(row[time_idx], '%Y/%m/%d %H:%M:%S')
                try:
                    height = float(row[height_idx])
                    yaw = float(row[yaw_idx]) * np.pi / 180
                    pitch = float(row[pitch_idx]) * np.pi / 180
                    roll = float(row[roll_idx]) * np.pi / 180
                    rotation = (yaw, pitch, roll)
                    latitude = float(row[latitude_idx])
                    longitude = float(row[longitude_idx])
                    pos = (latitude, longitude)
                    is_video = True if row[is_video_idx] else False
                except ValueError:
                    continue
                log_data = log_data_tuple(time_stamp, height, rotation, pos, is_video)
                drone_log_data.append(log_data)
    return drone_log_data


def get_video_data(project, video_file):
    file = os.path.join('.', 'projects', project, video_file)
    ffprobe_res = ffmpeg.probe(file, cmd='ffprobe')
    duration = float(ffprobe_res['format']['duration'])
    nb_frames = int(ffprobe_res['streams'][0]['nb_frames'])
    video_size = (int(ffprobe_res['streams'][0]['width']), int(ffprobe_res['streams'][0]['height']))
    location_string = ffprobe_res['format']['tags']['location']
    match = re.match(r'([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)', location_string)
    if match:
        pos = (float(match.group(1)), float(match.group(2)))
    else:
        pos = None
    return duration, nb_frames, video_size, pos


def match_log_and_video(log_data, video_duration, video_position=None):
    time_stamp = [data.time for data in log_data]
    is_video = [data.is_video for data in log_data]
    position = [data.position for data in log_data]
    if video_position is not None:
        for video_range in get_video_ranges(is_video, time_stamp):
            idx = time_stamp.index(video_range[0])
            pos = position[idx]
            if pos == video_position:  # maybe not the best way
                return video_range[0]
    minimum = min([(abs((x[1] - x[0]).total_seconds() - video_duration), x[0]) for x in get_video_ranges(is_video, time_stamp)], key=lambda y: y[0])
    return minimum[1]


def get_log_plot(log_data):
    height_plot, yaw_plot, pitch_plot, roll_plot = get_log_plots(log_data)
    grid = gridplot([[height_plot, yaw_plot], [pitch_plot, roll_plot]])
    script, div = components(grid)
    return script, div


def get_log_plot_with_video(log_data, video_start, video_duration, video_frames):
    height_plot, yaw_plot, pitch_plot, roll_plot = get_log_plots(log_data)
    video_end_time = datetime.fromtimestamp(video_start.timestamp()+video_duration)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, top=1, fill_color='#00cc00')
    video_position_line1 = Span(location=video_start, dimension='height', line_color='red')
    height_plot.add_layout(video_box)
    height_plot.add_layout(video_position_line1)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, top=10, bottom=-10, fill_color='#00cc00')
    video_position_line2 = Span(location=video_start, dimension='height', line_color='red')
    yaw_plot.add_layout(video_box)
    yaw_plot.add_layout(video_position_line2)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, bottom=5, fill_color='#00cc00')
    video_position_line3 = Span(location=video_start, dimension='height', line_color='red')
    pitch_plot.add_layout(video_box)
    pitch_plot.add_layout(video_position_line3)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, top=1, bottom=-1, fill_color='#00cc00')
    video_position_line4 = Span(location=video_start, dimension='height', line_color='red')
    roll_plot.add_layout(video_box)
    roll_plot.add_layout(video_position_line4)
    args = dict(span1=video_position_line1,
                span2=video_position_line2,
                span3=video_position_line3,
                span4=video_position_line4,
                video_start_time=video_start,
                video_duration=video_duration,
                video_frames=video_frames)
    callback = update_video_plot(args)
    height_plot.js_on_event('tap', callback)
    yaw_plot.js_on_event('tap', callback)
    pitch_plot.js_on_event('tap', callback)
    roll_plot.js_on_event('tap', callback)
    grid = gridplot([[height_plot, yaw_plot], [pitch_plot, roll_plot]])
    script, div = components(grid)
    return script, div


def get_log_plots(log_data):
    time_stamp = [data.time for data in log_data]
    height = [data.height for data in log_data]
    yaw = shift_yaw([data.rotation[0] * 180 / np.pi for data in log_data])
    pitch = [data.rotation[1] * 180 / np.pi for data in log_data]
    roll = [data.rotation[2] * 180 / np.pi for data in log_data]
    is_video = [data.is_video for data in log_data]
    height_plot = figure(title='Height', plot_width=700, plot_height=500)
    height_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    height_plot.yaxis.axis_label = 'Meters'
    height_plot.line(time_stamp, height)
    yaw_plot = figure(title='Yaw', plot_width=700, plot_height=500, x_range=height_plot.x_range)
    yaw_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    yaw_plot.yaxis.axis_label = 'Degrees'
    yaw_plot.line(time_stamp, yaw)
    pitch_plot = figure(title='Pitch', plot_width=700, plot_height=500, x_range=height_plot.x_range)
    pitch_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    pitch_plot.yaxis.axis_label = 'Degrees'
    pitch_plot.line(time_stamp, pitch)
    roll_plot = figure(title='Roll', plot_width=700, plot_height=500, x_range=height_plot.x_range)
    roll_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    roll_plot.yaxis.axis_label = 'Degrees'
    roll_plot.line(time_stamp, roll)
    for video_range in get_video_ranges(is_video, time_stamp):
        video_box1 = BoxAnnotation(left=video_range[0], right=video_range[1], fill_color='#cccccc')
        video_box2 = BoxAnnotation(left=video_range[0], right=video_range[1], fill_color='#cccccc')
        video_box3 = BoxAnnotation(left=video_range[0], right=video_range[1], fill_color='#cccccc')
        video_box4 = BoxAnnotation(left=video_range[0], right=video_range[1], fill_color='#cccccc')
        height_plot.add_layout(video_box1)
        yaw_plot.add_layout(video_box2)
        pitch_plot.add_layout(video_box3)
        roll_plot.add_layout(video_box4)
    return height_plot, yaw_plot, pitch_plot, roll_plot


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


def shift_yaw(yaw):
    new_yaw = []
    last_point = 0
    shift = 0
    for point in yaw:
        if (last_point > 150 and point < -150) or (last_point < -150 and point > 150):
            if point < 0:
                shift += 360
            else:
                shift -= 360
        new_point = point + shift
        last_point = point
        new_yaw.append(new_point)
    return new_yaw


def remove_null_bytes(log):
    with open(log, 'rb') as fi:
        data = fi.read()
    with open(log, 'wb') as fo:
        fo.write(data.replace(b'\x00', b''))


def update_video_plot(dict_arguments):
    return CustomJS(args=dict_arguments, code="""
    var video_time = video_start_time + current_frame/video_frames*video_duration*1000
    span1.location = video_time
    span2.location = video_time
    span3.location = video_time
    span4.location = video_time
    """)
