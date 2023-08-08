import os
import random
import logging
import flask
from drone.drone_log_data import drone_log
from forms import NewProjectForm, EditProjectForm
from drone import plot_log_data
from app_config import data_dir, get_random_filename, Project, Drone, db
from helper_functions import get_all_annotations, save_annotations_csv


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
    return flask.send_file(filename, as_attachment=True)


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


def remove_file(f):
    if f:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass
