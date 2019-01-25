import os
import csv
from collections import namedtuple
import flask
from forms import NewDroneForm, EditDroneForm
from help_functions import get_last_updated_time_as_string, get_last_modified_time

# todo add camera calibration

drones_view = flask.Blueprint('drones', __name__)
drone_tuple = namedtuple('drone', ['title', 'camera_settings', 'vfov', 'hfov', 'last_updated'])


@drones_view.route('/drones', methods=['GET', 'POST'])
def index():
    drone_dict = make_drone_dict()
    drone_form = get_drone_form(drone_dict)
    edit_drone_form = get_edit_drone_form(drone_dict)
    return flask.render_template('drones/index.html', drones=drone_dict, new_drone_form=drone_form, edit_drone_form=edit_drone_form)


def get_drone_form(drone_dict):
    form = NewDroneForm()
    if form.validate_on_submit():
        drone_title = form.name.data
        camera_settings = form.camera_settings.data
        vfov = form.vfov.data
        hfov = form.hfov.data
        if drone_title in drone_dict:
            flask.flash('A project with that name already exist!')
        else:
            with open(os.path.join('.', 'drones',  drone_title + '.txt'), 'w') as file:
                writer = csv.writer(file)
                header = ('title', 'camera_settings', 'vfov', 'hfov')
                writer.writerow(header)
                writer.writerow((drone_title, camera_settings, vfov, hfov))
            drone = drone_tuple(drone_title, camera_settings, vfov, hfov, get_last_updated_time_as_string(0))
            drone_dict.update({drone.title: drone})
    return form


def get_edit_drone_form(drone_dict):
    form = EditDroneForm()
    if form.validate_on_submit():
        project_before = form.edit_drone_before.data
        drone_title = form.edit_name.data
        camera_settings = form.edit_camera_settings.data
        vfov = form.edit_vfov.data
        hfov = form.edit_hfov.data
        if drone_title in drone_dict and not drone_title == project_before:
            flask.flash('A project with that name already exist!')
        else:
            drone_dict.pop(project_before, None)
            os.rename(os.path.join('.', 'drones', project_before + '.txt'), os.path.join('.', 'drones', drone_title + '.txt'))
            with open(os.path.join('.', 'drones', drone_title + '.txt'), 'w') as file:
                writer = csv.writer(file)
                header = ('title', 'camera_settings', 'vfov', 'hfov')
                writer.writerow(header)
                writer.writerow((drone_title, camera_settings, vfov, hfov))
            drone = drone_tuple(drone_title, camera_settings, vfov, hfov, get_last_updated_time_as_string(0))
            drone_dict.update({drone.title: drone})
    return form


def make_drone_dict():
    drone_dict = {}
    drones = next(os.walk(os.path.join('.', 'drones')))[2]
    for drone_title in drones:
        last_modified_string = get_last_modified_time('drones', drone_title)
        with open(os.path.join('.', 'drones', drone_title), 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                drone = drone_tuple(row.get('title'), row.get('camera_settings'), row.get('vfov'), row.get('hfov'), last_modified_string)
                drone_dict.update({drone.title: drone})
    return drone_dict


@drones_view.route('/drones/<drone>/calibrate')
def add_calibration(drone):
    return str(drone)


@drones_view.route('/drones/<drone>/remove')
def remove_drone(drone):
    drone_file = os.path.join('.', 'drones', drone + '.txt')
    os.remove(drone_file)
    return flask.redirect(flask.url_for('drones.index'))
