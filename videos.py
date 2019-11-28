import os
import json
import flask

from datetime import datetime, time
from drone_log_data import drone_log
from fov import fov
from help_functions import base_dir, horizon_dict
from annotations import Annotations
import plot_log_data

annotation_class = Annotations(drone_log, fov)
videos_view = flask.Blueprint('videos', __name__)


@videos_view.route('/<project>/plot')
def plot_log(project):
    drone_log.get_log_data(project)
    plot_script, plot_div = plot_log_data.get_log_plot(drone_log.log_data())
    return flask.render_template('videos/plot.html', plot_div=plot_div, plot_script=plot_script, project=project)


@videos_view.route('/<project>/<video_file>/annotate')
def video(project, video_file):
    mat_file = os.path.join(base_dir, 'projects', project, 'drone.cam.npz')
    fov.set_camera_params(mat_file)
    drone_log.get_log_data(project)
    drone_log.get_video_data(project, video_file)
    fov.set_image_size(*drone_log.video_size)
    video_info_file = os.path.join(base_dir, 'projects', project, video_file + '.txt')
    if os.path.isfile(video_info_file):
        with open(video_info_file) as v_file:
            timestamp = v_file.read()
            video_start_time = datetime.fromtimestamp(float(timestamp))
            drone_log.video_start_time = video_start_time
    else:
        video_start_time, message = drone_log.match_log_and_video()
        if message:
            flask.flash(message, 'warning')
        with open(video_info_file, 'w') as v_file:
            v_file.write(str(video_start_time.timestamp()))
    plot_script, plot_div = plot_log_data.get_log_plot_with_video(drone_log.log_data(), video_start_time, drone_log.video_duration, drone_log.video_nb_frames)
    json_filename = os.path.join(base_dir, 'projects', project, video_file + '.json')
    if os.path.isfile(json_filename):
        with open(json_filename, 'r') as json_file:
            json_data = json.load(json_file)
    else:
        json_data = None
    args = dict(project=project,
                video=video_file,
                json_data=json_data,
                plot_script=plot_script,
                plot_div=plot_div,
                video_width=drone_log.video_size[0],
                video_height=drone_log.video_size[1],
                num_frames=drone_log.video_nb_frames,
                fps=drone_log.video_nb_frames / drone_log.video_duration,
                video_start_time=video_start_time)
    return flask.render_template('videos/video.html', **args)


@videos_view.route('/<project>/<video_file>/save', methods=['POST'])
def save_fabric_json(project, video_file):
    json_data = json.loads(flask.request.form.get('fabric_json'))
    file_name = os.path.join(base_dir, 'projects', project, video_file + '.json')
    with open(file_name, 'w') as json_file:
        json.dump(json_data, json_file)
    return ''


@videos_view.route('/add_marking', methods=['POST'])
def add_marking():
    global annotation_class
    add_name = flask.request.form.get('add_name')
    if add_name == 'true':
        name = flask.request.form.get('name')
        annotation_class.add_name(name)
    else:
        fabric_json = flask.request.form.get('fabric_json')
        annotation_class.from_fabric_json(fabric_json)
    return flask.jsonify(annotation_class.to_json())


@videos_view.route('/get_horizon_fabricjs', methods=['POST'])
def get_horizon_fabricjs():
    frame = int(flask.request.form.get('frame'))
    _, _, rotation, _ = drone_log.get_log_data_from_frame(frame)
    horizon_points = fov.get_horizon_and_world_corners(horizon_dict, rotation)
    return flask.jsonify(horizon_points)


@videos_view.route('/<project>/<video_file>/save_start_time', methods=['POST'])
def save_start_time(project, video_file):
    start_time_str = flask.request.form.get('start_time')
    start_time = time(int(start_time_str[:2]), int(start_time_str[3:5]), int(start_time_str[6:8]), int(start_time_str[9:]))
    video_info_file = os.path.join(base_dir, 'projects', project, video_file + '.txt')
    with open(video_info_file) as v_file:
        timestamp = v_file.read()
        video_start_time = datetime.fromtimestamp(float(timestamp))
    new_video_start_time = datetime.combine(video_start_time, start_time)
    with open(video_info_file, 'w') as v_file:
        v_file.write(str(new_video_start_time.timestamp()))
    drone_log.video_start_time = new_video_start_time
    return ''
