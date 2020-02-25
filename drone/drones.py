import os
import re
import shutil
import numpy as np
import flask
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from forms import NewDroneForm, EditDroneForm
from app_config import data_dir, db
from calibration.calibration import CalibrateCamera

logger = logging.getLogger('app.' + __name__)
drones_view = flask.Blueprint('drones', __name__)


class Drone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.Text())
    calibration = db.Column(db.PickleType())
    last_update = db.Column(db.DateTime())

    def __repr__(self):
        return f'<Drone {self.name}>'


@drones_view.route('/drones', methods=['GET', 'POST'])
def index():
    drone_form = get_drone_form()
    edit_drone_form = get_edit_drone_form()
    drones = Drone.query.all()
    logger.debug(f'Render drone index')
    return flask.render_template('drones/index.html', drones=drones, new_drone_form=drone_form, edit_drone_form=edit_drone_form)


def get_drone_form():
    drones = Drone.query.all()
    form = NewDroneForm()
    if form.validate_on_submit():
        drone_name = form.name.data
        camera_settings = form.camera_settings.data
        if drone_name in [x.name for x in drones]:
            flask.flash('A drone with that name already exist!')
        else:
            drone = Drone(name=drone_name, description=camera_settings, last_update=datetime.now())
            db.session.add(drone)
            db.session.commit()
    return form


def get_edit_drone_form():
    drones = Drone.query.all()
    form = EditDroneForm()
    if form.validate_on_submit():
        drone_id = form.edit_drone_id.data
        drone_name_before = form.edit_drone_before.data
        new_drone_name = form.edit_name.data
        new_camera_settings = form.edit_camera_settings.data
        drone = Drone.query.get_or_404(drone_id)
        if drone.name in [x.name for x in drones] and not drone.name == drone_name_before:
            flask.flash('A drone with that name already exist!')
        else:
            drone.name = new_drone_name
            drone.description = new_camera_settings
            drone.last_update = datetime.now()
            db.session.commit()
    return form


@drones_view.route('/drones/<drone_id>/calibrate', methods=['GET', 'POST'])
def add_calibration(drone_id):
    calibration_folder = os.path.join(data_dir, 'calibration')
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
    return flask.render_template('drones/calibration.html', drone=drone_id)


@drones_view.route('/dones/<drone_id>/do_calibration', methods=['POST'])
def do_calibration(drone_id):
    logger.debug(f'do_calibration is called for drone {drone_id}')
    calibrate_cam = CalibrateCamera()
    in_folder = os.path.join(data_dir, 'calibration')
    try:
        result = calibrate_cam(in_folder)
        if result == -1:
            return json.dumps([{'type': 'danger', 'message': 'Error finding checkerboard during calibration! Please try again with new images or new video by reloading the page.'}])
        if not result:
            return json.dumps([{'type': 'danger', 'message': 'Error no video or images found! Please try again by reloading the page.'}])
        drone = Drone.query.get_or_404(drone_id)
        drone.calibration = result
        drone.last_update = datetime.now()
        db.session.commit()
    except AttributeError:
        logger.debug(f'calibrate_cam throws an Attribute Error')
        return json.dumps([{'type': 'danger', 'message': 'Error loading images or video. Please try again by reloading the page.'}])
    return 'true'


@drones_view.route('/drones/<drone_id>/view_calibration')
def view_calibration(drone_id):
    drone = Drone.query.get_or_404(drone_id)
    mtx, dist, fov_x, fov_y = drone.calibration
    logger.debug(f'Render view_calibration')
    return flask.render_template('drones/view_calibration.html', mtx=np.around(mtx, 1), dist=np.around(dist, 5), fov_x=np.round(fov_x, 2), fov_y=np.round(fov_y, 2))


@drones_view.route('/drones/<drone_id>/remove')
def remove_drone(drone_id):
    logger.debug(f'Removing drone {drone_id}')
    drone = Drone.query.get_or_404(drone_id)
    os.remove(drone.cal_file)
    db.session.delete(drone)
    db.session.commit()
    return flask.redirect(flask.url_for('drones.index'))
