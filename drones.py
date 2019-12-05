import os
import csv
import re
import shutil
import numpy as np
from collections import namedtuple
import flask
import json
import logging
from werkzeug.utils import secure_filename
from forms import NewDroneForm, EditDroneForm
from help_functions import get_last_updated_time_as_string, get_last_modified_time, base_dir
from calibration import CalibrateCamera

logger = logging.getLogger('app.' + __name__)


drones_view = flask.Blueprint('drones', __name__)
drone_tuple = namedtuple('drone', ['title', 'camera_settings', 'calibrated', 'last_updated'])


@drones_view.route('/drones', methods=['GET', 'POST'])
def index():
    drone_dict = make_drone_dict()
    drone_form = get_drone_form(drone_dict)
    edit_drone_form = get_edit_drone_form(drone_dict)
    logger.debug(f'Render drone index')
    return flask.render_template('drones/index.html', drones=drone_dict, new_drone_form=drone_form, edit_drone_form=edit_drone_form)


def get_drone_form(drone_dict):
    form = NewDroneForm()
    if form.validate_on_submit():
        drone_title = form.name.data
        camera_settings = form.camera_settings.data
        if drone_title in drone_dict:
            flask.flash('A project with that name already exist!')
        else:
            with open(os.path.join(base_dir, 'drones',  drone_title + '.txt'), 'w') as file:
                writer = csv.writer(file)
                header = ('title', 'camera_settings')
                writer.writerow(header)
                writer.writerow((drone_title, camera_settings))
            drone = drone_tuple(drone_title, camera_settings, False, get_last_updated_time_as_string(0))
            drone_dict.update({drone.title: drone})
    return form


def get_edit_drone_form(drone_dict):
    form = EditDroneForm()
    if form.validate_on_submit():
        project_before = form.edit_drone_before.data
        drone_title = form.edit_name.data
        camera_settings = form.edit_camera_settings.data
        if drone_title in drone_dict and not drone_title == project_before:
            flask.flash('A project with that name already exist!')
        else:
            calibrated = drone_dict.get(project_before).calibrated
            drone_dict.pop(project_before, None)
            os.rename(os.path.join(base_dir, 'drones', project_before + '.txt'), os.path.join(base_dir, 'drones', drone_title + '.txt'))
            with open(os.path.join(base_dir, 'drones', drone_title + '.txt'), 'w') as file:
                writer = csv.writer(file)
                header = ('title', 'camera_settings')
                writer.writerow(header)
                writer.writerow((drone_title, camera_settings))
            drone = drone_tuple(drone_title, camera_settings, calibrated, get_last_updated_time_as_string(0))
            drone_dict.update({drone.title: drone})
    return form


def make_drone_dict():
    drone_dict = {}
    drones = next(os.walk(os.path.join(base_dir, 'drones')))[2]
    for drone_title in drones:
        if drone_title.endswith('.txt'):
            last_modified_string = get_last_modified_time('drones', drone_title)
            calibrated = True if os.path.isfile(os.path.join(base_dir, 'drones', drone_title[:-4] + '.cam.npz')) else False
            with open(os.path.join(base_dir, 'drones', drone_title), 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    drone = drone_tuple(row.get('title'), row.get('camera_settings'), calibrated, last_modified_string)
                    drone_dict.update({drone.title: drone})
    return drone_dict


@drones_view.route('/drones/<drone>/calibrate', methods=['GET', 'POST'])
def add_calibration(drone):
    calibration_folder = os.path.join(base_dir, 'drones', 'calibration')
    if not os.path.exists(calibration_folder):
        logger.debug(f'Creating calibration folder')
        os.mkdir(calibration_folder)
    if os.path.isdir(calibration_folder):
        logger.debug(f'Removing calibration folder')
        shutil.rmtree(calibration_folder)
        logger.debug(f'Creating calibration folder')
        os.mkdir(calibration_folder)
    if flask.request.method == 'POST':
        file_obj = flask.request.files
        for file in file_obj.values():
            file_location = os.path.join(calibration_folder, secure_filename(file.filename))
            image_mimetype = re.compile('image/*')
            video_mimetype = re.compile('video/*')
            if image_mimetype.match(file.mimetype) or video_mimetype.match(file.mimetype):
                file.save(file_location)
                logger.debug(f'Saving file: {file_location}')
    logger.debug(f'Render drone calibration for {flask.request.method} request')
    return flask.render_template('drones/calibration.html', drone=drone)


@drones_view.route('/dones/<drone>/do_calibration', methods=['POST'])
def do_calibration(drone):
    logger.debug(f'do_calibration is called for drone {drone}')
    calibrate_cam = CalibrateCamera()
    in_folder = os.path.join(base_dir, 'drones', 'calibration')
    save_file = os.path.join(base_dir, 'drones', drone + '.cam')
    try:
        success = calibrate_cam(in_folder, save_file)
        if success == -1:
            return json.dumps([{'type': 'danger', 'message': 'Error finding checkerboard during calibration! Please try again with new images or new video by reloading the page.'}])
        if not success:
            return json.dumps([{'type': 'danger', 'message': 'Error no video or images found! Please try again by reloading the page.'}])
    except AttributeError:
        logger.debug(f'calibrate_cam throws an Attribute Error')
        return json.dumps([{'type': 'danger', 'message': 'Error loading images or video. Please try again by reloading the page.'}])
    return 'true'


@drones_view.route('/drones/<drone>/view_calibration')
def view_calibration(drone):
    cam_file = os.path.join(base_dir, 'drones', drone + '.cam.npz')
    np_file = np.load(cam_file)
    mtx = np_file['mtx']
    dist = np_file['dist']
    fov_x = np_file['fov_x']
    fov_y = np_file['fov_y']
    logger.debug(f'Render view_calibration')
    return flask.render_template('drones/view_calibration.html', mtx=np.around(mtx, 1), dist=np.around(dist, 5), fov_x=np.round(fov_x, 2), fov_y=np.round(fov_y, 2))


@drones_view.route('/drones/<drone>/remove')
def remove_drone(drone):
    logger.debug(f'Removing drone {drone}')
    drone_file = os.path.join(base_dir, 'drones', drone + '.txt')
    os.remove(drone_file)
    return flask.redirect(flask.url_for('drones.index'))
