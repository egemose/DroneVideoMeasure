from datetime import datetime
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.models import DatetimeTickFormatter, BoxAnnotation, Span, CustomJS
from bokeh.plotting import figure
from drone.drone_log_data import get_video_ranges
import logging

logger = logging.getLogger('app.' + __name__)


def get_log_plot(log_data):
    logger.debug(f'Getting log plot')
    height_plot, yaw_plot, pitch_plot, roll_plot = _get_log_plots(log_data)
    grid = gridplot([height_plot, yaw_plot, pitch_plot, roll_plot], ncols=1, sizing_mode="scale_width")
    script, div = components(grid)
    return script, div


def get_log_plot_with_video(log_data, video_start, video_duration, video_frames):
    """
    Arrange the log file plots and add annotations to them that shows 
    the current time in the video and the duration of the current video.
    """
    logger.debug(f'Getting log plot with video')
    height_plot, yaw_plot, pitch_plot, roll_plot = _get_log_plots(log_data)
    video_end_time = datetime.fromtimestamp(video_start.timestamp()+video_duration)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, top=1, fill_color='#00cc00')
    video_position_line1 = Span(location=video_start, dimension='height', line_color='red')
    height_plot.add_layout(video_box)
    height_plot.add_layout(video_position_line1)
    video_box = BoxAnnotation(left=video_start, right=video_end_time, top=yaw_plot.y_range.end, bottom=yaw_plot.y_range.start, fill_color='#00cc00')
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
    callback = _update_video_plot(args)
    height_plot.js_on_event('tap', callback)
    yaw_plot.js_on_event('tap', callback)
    pitch_plot.js_on_event('tap', callback)
    roll_plot.js_on_event('tap', callback)
    grid = gridplot([height_plot, yaw_plot, pitch_plot, roll_plot], ncols=1, sizing_mode="scale_width")
    script, div = components(grid)
    return script, div


def _get_log_plots(log_data):
    """Make plots for visualizing data from the drone log file."""
    time_stamp = log_data[0]
    height = log_data[1]
    yaw = _shift_yaw(log_data[2])
    pitch = log_data[3]
    roll = log_data[4]
    is_video = log_data[5]
    height_plot = figure(title='Height', width=700, height=500)
    height_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    height_plot.yaxis.axis_label = 'Meters'
    height_plot.line(time_stamp, height)
    yaw_plot = figure(title='Yaw', width=700, height=500, x_range=height_plot.x_range)
    yaw_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    yaw_plot.yaxis.axis_label = 'Degrees'
    yaw_plot.line(time_stamp, yaw)
    pitch_plot = figure(title='Pitch', width=700, height=500, x_range=height_plot.x_range)
    pitch_plot.xaxis.formatter = DatetimeTickFormatter(minsec=['%H:%M:%S'], minutes=['%H:%M:%S'], hourmin=['%H:%M:%S'])
    pitch_plot.yaxis.axis_label = 'Degrees'
    pitch_plot.line(time_stamp, pitch)
    roll_plot = figure(title='Roll', width=700, height=500, x_range=height_plot.x_range)
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


def _update_video_plot(dict_arguments):
    return CustomJS(args=dict_arguments, code="""
    var video_time = video_start_time + current_frame/video_frames*video_duration*1000
    span1.location = video_time
    span2.location = video_time
    span3.location = video_time
    span4.location = video_time
    """)


def _shift_yaw(yaw):
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
