import json
import os
import re
import numpy as np
from collections import defaultdict
from datetime import datetime, time
import flask
import logging
from drone import plot_log_data
from drone.drone_log_data import drone_log
from drone.fov import fov
from app_config import data_dir, Project, Video, Drone, db
from video.annotations import Annotations

logger = logging.getLogger('app.' + __name__)
annotation_class = Annotations(drone_log, fov)
videos_view = flask.Blueprint('videos', __name__)


def get_horizon_dict():
    world_points = defaultdict(list)
    for x in np.linspace(-np.pi, np.pi, 100):
        point = (0, np.cos(x), np.sin(x))
        world_points['NS'].append(point)
    for x in np.linspace(-np.pi, np.pi, 100):
        point = (np.cos(x), 0, np.sin(x))
        world_points['EW'].append(point)
    for x in np.linspace(-np.pi, np.pi, 100):
        point = (np.cos(x), np.sin(x), 0)
        world_points['pitch0'].append(point)
    for x in np.linspace(-np.pi, np.pi, 100):
        point = (np.cos(x) / np.sqrt(2), np.sin(x) / np.sqrt(2), -1 / np.sqrt(2))
        world_points['pitch45'].append(point)
    return world_points


horizon_dict = get_horizon_dict()


@videos_view.route('/<video_id>/annotate')
def video(video_id):
    logger.debug(f'Video called with video: {video_id}')
    video = Video.query.get_or_404(video_id)
    project = Project.query.get_or_404(video.project_id)
    drone = Drone.query.get_or_404(project.drone_id)
    fov.set_camera_params(*drone.calibration)
    log_file = os.path.join(data_dir, project.log_file)
    drone_log.get_log_data(log_file)
    drone_log.set_video_data(video.duration, video.frames, (video.width, video.height), (video.latitude, video.longitude))
    fov.set_image_size(*drone_log.video_size)
    json_data = video.json_data if video.json_data is str else '{}'
    video_start_time = video.start_time
    if video_start_time:
        drone_log.video_start_time = video_start_time
    else:
        video_start_time, message = drone_log.match_log_and_video()
        if message:
            flask.flash(message, 'warning')
        video.start_time = video_start_time
        db.session.commit()
    plot_script, plot_div = plot_log_data.get_log_plot_with_video(drone_log.log_data(), video_start_time, drone_log.video_duration, drone_log.video_nb_frames)
    args = dict(project_id=project.id,
                video=video,
                json_data=json.loads(json_data),
                plot_script=plot_script,
                plot_div=plot_div,
                video_width=drone_log.video_size[0],
                video_height=drone_log.video_size[1],
                num_frames=drone_log.video_nb_frames,
                fps=drone_log.video_nb_frames / drone_log.video_duration,
                video_start_time=video_start_time)
    logger.debug(f'Render video {video.file}')
    return flask.render_template('videos/video.html', **args)


@videos_view.route('/<video_id>/save', methods=['POST'])
def save_fabric_json(video_id):
    logger.debug(f'Saving annotations to json file for {video_id}')
    json_data = flask.request.form.get('fabric_json')
    print(json_data)
    video = Video.query.get_or_404(video_id)
    video.json_data = json_data
    db.session.commit()
    return ''


@videos_view.route('/markings_modified', methods=['POST'])
def markings_modified():
    logger.debug(f'markings_modified called')
    fabric_json = flask.request.form.get('fabric_json')
    annotation_class.from_fabric_json(fabric_json)
    return flask.jsonify(annotation_class.tree_json)



@videos_view.route('/get_horizon_fabricjs', methods=['POST'])
def get_horizon_fabricjs():
    logger.debug(f'get_horizon_fabricjs called')
    frame = int(flask.request.form.get('frame'))
    _, _, rotation, _ = drone_log.get_log_data_from_frame(frame)
    horizon_points = fov.get_horizon_and_world_corners(horizon_dict, rotation)
    return flask.jsonify(horizon_points)


@videos_view.route('/<video_id>/save_start_time', methods=['POST'])
def save_start_time(video_id):
    logger.debug(f'save_start_time called for {video_id}')
    start_time_str = flask.request.form.get('start_time')
    match = re.fullmatch(r'(\d\d):(\d\d):(\d\d)\.?(\d*)', start_time_str)
    video = Video.query.get_or_404(video_id)
    if match:
        start_time = time(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4) if match.group(4) else 0))
        video_start_time = video.start_time
        new_video_start_time = datetime.combine(video_start_time, start_time)
        video.start_time = new_video_start_time
        db.session.commit()
        drone_log.video_start_time = new_video_start_time
    elif not start_time_str:
        video_start_time, message = drone_log.match_log_and_video()
        if message:
            flask.flash(message, 'warning')
        video.start_time = new_video_start_time
        db.session.commit()
    else:
        flask.flash('Error setting the video time.', 'error')
        logger.debug(f'Error setting the video time')
    return ''
