import csv
import json
import os
import random
import logging
import flask
import numpy as np
from drone.drone_log_data import drone_log
from forms import NewProjectForm, EditProjectForm
from drone.fov import fov
from drone import plot_log_data
from app_config import data_dir, get_random_filename, Project, Drone, db


logger = logging.getLogger('app.' + __name__)
projects_view = flask.Blueprint('projects', __name__)


@projects_view.route('/projects', methods=['GET', 'POST'])
def projects():
    random_int = random.randint(1, 10000000)
    res, new_project_form = get_new_project_form()
    if res:
        return res
    edit_project_form = get_edit_project_form()
    projects = Project.query.all()
    drones = Drone.query.all()
    drones = [(x.id, x.name) for x in drones if x.calibration]
    arguments = {'projects': projects, 'drones': drones, 'random_int': random_int, 'new_project_form': new_project_form, 'edit_project_form': edit_project_form}
    logger.debug(f'Render index')
    return flask.render_template('projects/projects.html', **arguments)


def get_new_project_form():
    form = NewProjectForm()
    drones = Drone.query.all()
    form.drone.choices = [(x.id, x.name) for x in drones if x.calibration]
    if form.validate_on_submit():
        project_title = form.name.data
        description = form.description.data
        drone_id = form.drone.data
        projects = Project.query.all()
        if project_title in [x.name for x in projects]:
            flask.flash('A project with that name already exist!')
        else:
            logger.debug(f'Creating project with name {project_title}')
            log_file = None
            if form.log_file.data:
                log_error = None
                log_filename = get_random_filename(form.log_file.data.filename)
                log_file = os.path.join(data_dir, log_filename)
                form.log_file.data.save(log_file)
                success = drone_log.test_log(log_file)
                if not success:
                    remove_file(log_file)
                    log_filename = None
                    log_error = 'Error interpreting the drone log file. Try and upload the log file again.'
            else:
                log_error = 'No drone log file added. Please add a log file.'
            project = Project(name=project_title, description=description, drone_id=drone_id, log_file=log_file, log_error=log_error)
            db.session.add(project)
            db.session.commit()
            return flask.redirect(flask.url_for('projects.projects', project_id=project.id)), form
    return None, form


def get_edit_project_form():
    form = EditProjectForm()
    drones = Drone.query.all()
    form.edit_drone.choices = [(x.id, x.name) for x in drones]
    projects = Project.query.all()
    if form.validate_on_submit():
        project_id = form.edit_project_id.data
        project_before = form.edit_project_before.data
        project_title = form.edit_name.data
        description = form.edit_description.data
        drone_id = form.edit_drone.data
        logger.debug(f'Editing project {project_before} with new name {project_title}')
        if project_title in projects and not project_title == project_before:
            flask.flash('A project with that name already exist!')
        else:
            project = Project.query.get_or_404(project_id)
            project.name = project_title
            project.description = description
            project.drone_id = drone_id
            if form.edit_log_file.data:
                remove_file(project.log_file)
                log_error = None
                log_filename = get_random_filename(form.edit_log_file.data.filename)
                log_file = os.path.join(data_dir, log_filename)
                form.edit_log_file.data.save(log_file)
                success = drone_log.test_log(log_file)
                if success:
                    project.log_file = log_file
                else:
                    remove_file(log_file)
                    project.log_file = None
                    log_error = 'Error interpreting the drone log file. Try and upload the log file again.'
                project.log_error = log_error
            db.session.commit()
    return form


@projects_view.route('/projects/<project_id>/plot')
def plot_log(project_id):
    project = Project.query.get_or_404(project_id)
    drone_log.get_log_data(project.log_file)
    plot_script, plot_div = plot_log_data.get_log_plot(drone_log.log_data())
    logger.debug(f'Render video plot for {project_id}')
    return flask.render_template('projects/plot.html', plot_div=plot_div, plot_script=plot_script, project_id=project_id)


@projects_view.route('/projects/<project_id>/download')
def download(project_id):
    with open('version.txt') as version_file:
        pro_version = version_file.read()
    project = Project.query.get_or_404(project_id)
    annotations = get_all_annotations(project, pro_version)
    filename = os.path.join(data_dir, 'annotations.csv')
    save_annotations_csv(annotations, filename)
    logger.debug(f'Sending annotations.csv to user.')
    return flask.send_file(filename, as_attachment=True, attachment_filename='annotations.csv')


def save_annotations_csv(annotations, filename):
    logger.debug(f'Saving annotations in {filename}')
    with open(filename, 'w') as fp:
        csv_writer = csv.writer(fp, delimiter=',')
        header = ('name', 'time', 'length', 'lat', 'lon', 'east', 'north', 'zone number', 'zone letter',
                  'image_x', 'image_y', 'video', 'project', 'pro. version')
        csv_writer.writerow(header)
        for annotation in annotations:
            if annotation:
                csv_writer.writerow(annotation)


def get_all_annotations(project, pro_version):
    logger.debug(f'Getting all annotations')
    annotations = []
    drone = Drone.query.get_or_404(project.drone_id)
    fov.set_camera_params(*drone.calibration)
    drone_log.get_log_data(project.log_file)
    for video in project.videos:
        json_data = json.loads(video.json_data)
        objects = json_data['objects']
        objects = json_data['objects']
        drone_log.set_video_data(video.duration, video.frames, (video.width, video.height), (video.latitude, video.longitude))
        fov.set_image_size(*drone_log.video_size)
        drone_log.match_log_and_video()
        if objects:
            for obj in objects:
                if obj['type'] == 'FrameLine' or obj['type'] == 'FramePoint':
                    annotation = get_frame_obj_data(obj)
                    annotation.extend([video.file, project.name, pro_version])
                else:
                    logger.debug(f'Unknown annotation found of type: {obj["type"]}')
                    annotation = None
                annotations.append(annotation)
    return annotations


def get_frame_obj_data(obj):
    name = obj.get('name')
    log_data = drone_log.get_log_data_from_frame(obj.get('frame'))
    if obj['type'] == 'FrameLine':
        x1 = obj.get('x1')
        x2 = obj.get('x2')
        y1 = obj.get('y1')
        y2 = obj.get('y2')
        xoffset = obj.get('left') + obj.get('width') / 2
        yoffset = obj.get('top') + obj.get('height') / 2
        image_point1 = (x1 + xoffset, y1 + yoffset)
        image_point2 = (x2 + xoffset, y2 + yoffset)
        image_point = ((image_point1[0] + image_point2[0]) / 2, (image_point1[1] + image_point2[1]) / 2)
        wp1, zone = fov.get_world_point(image_point1, *log_data[1:], return_zone=True)
        wp2 = fov.get_world_point(image_point2, *log_data[1:])
        wp = ((wp1[0] + wp2[0]) / 2, (wp1[1] + wp2[1]) / 2)
        length = np.sqrt((wp1[0] - wp2[0]) ** 2 + (wp1[1] - wp2[1]) ** 2)
    elif obj['type'] == 'FramePoint':
        image_point = (obj.get('left'), obj.get('top'))
        wp, zone = fov.get_world_point(image_point, *log_data[1:], return_zone=True)
        length = 0
    else:
        return None
    pos = fov.convert_utm(wp[0], wp[1], zone)
    annotation = [name, log_data[0], length, pos[0], pos[1], wp[0], wp[1], zone[0], zone[1], image_point[0], image_point[1]]
    return annotation


@projects_view.route('/projects/<project_id>/remove')
def remove_project(project_id):
    logger.debug(f'Removing project {project_id}')
    project = Project.query.get_or_404(project_id)
    remove_file(project.log_file)
    for video in project.videos:
        remove_file(video.file)
        remove_file(video.image)
        db.session.delete(video)
    db.session.delete(project)
    db.session.commit()
    return flask.redirect(flask.url_for('projects.projects'))


def remove_file(file):
    if file:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
