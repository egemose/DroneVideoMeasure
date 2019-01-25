import csv
import glob
import os
import shutil
import random
import subprocess
from collections import namedtuple
import ffmpeg
import flask
import json
from werkzeug.utils import secure_filename
from forms import NewProjectForm, EditProjectForm
import drone_log_data
from help_functions import get_last_modified_time, get_last_updated_time_as_string

# todo add warning when clear Annotations
# todo check if enter is hit what happens
# todo add conversion from fabricjs to csv

project_tuple = namedtuple('project', ['title', 'description', 'last_updated'])
projects_view = flask.Blueprint('projects', __name__)


@projects_view.route('/', methods=['GET', 'POST'])
def index():
    random_int = random.randint(1, 10000000)
    project_dict = make_project_dict()
    res, new_project_form = get_new_project_form(project_dict)
    if res:
        return res
    edit_project_form = get_edit_project_form(project_dict)
    return flask.render_template('projects/index.html', projects=project_dict, random_int=random_int, new_project_form=new_project_form, edit_project_form=edit_project_form)


def make_project_dict():
    project_dict = {}
    projects = next(os.walk(os.path.join('.', 'projects')))[1]
    for project_title in projects:
        last_modified_string = get_last_modified_time('projects', project_title)
        with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'r') as file:
            description = flask.Markup(file.read())
        project = project_tuple(project_title, description, last_modified_string)
        project_dict.update({project_title: project})
    return project_dict


def get_new_project_form(project_dict):
    form = NewProjectForm()
    drones = next(os.walk(os.path.join('.', 'drones')))[2]
    form.drone.choices = [(d, d[:-4]) for d in drones]
    if form.validate_on_submit():
        project_title = form.name.data
        description = form.description.data
        drone = form.drone.data
        if project_title in project_dict:
            flask.flash('A project with that name already exist!')
        else:
            os.mkdir(os.path.join('.', 'projects', project_title))
            with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'w') as file:
                file.write(description)
            shutil.copyfile(os.path.join('.', 'drones', drone), os.path.join('.', 'projects', project_title, 'drone.txt'))
            log_file = os.path.join('.', 'projects', project_title, 'drone_log.txt')
            form.log_file.data.save(log_file)
            converted_log = os.path.join('.', 'projects', project_title, 'drone_log.csv')
            cmd = 'wine drone_log/TXTlogToCSVtool "' + log_file + '" "' + converted_log + '"'
            subprocess.call(cmd, shell=True)
            return flask.redirect(flask.url_for('projects.upload', project=project_title)), form
    return None, form


def get_edit_project_form(project_dict):
    form = EditProjectForm()
    drones = next(os.walk(os.path.join('.', 'drones')))[2]
    form.edit_drone.choices = [(d, d[:-4]) for d in drones]
    if form.validate_on_submit():
        project_before = form.edit_project_before.data
        description = form.edit_description.data
        project_title = form.edit_name.data
        drone = form.edit_drone.data
        if project_title in project_dict and not project_title == project_before:
            flask.flash('A project with that name already exist!')
        else:
            project_dict.pop(project_before, None)
            shutil.copyfile(os.path.join('.', 'drones', drone), os.path.join('.', 'projects', project_title, 'drone.txt'))
            os.rename(os.path.join('.', 'projects', project_before), os.path.join('.', 'projects', project_title))
            with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'w') as file:
                file.write(description)
            last_updated = get_last_updated_time_as_string(0)
            project = project_tuple(project_title, description, last_updated)
            project_dict.update({project_title: project})
            print(form.edit_log_file.data)
            if form.edit_log_file.data:
                log_file = os.path.join('.', 'projects', project_title, 'drone_log.txt')
                form.edit_log_file.data.save(log_file)
                converted_log = os.path.join('.', 'projects', project_title, 'drone_log.csv')
                cmd = 'wine drone_log/TXTlogToCSVtool "' + log_file + '" "' + converted_log + '"'
                subprocess.call(cmd, shell=True)
    return form


@projects_view.route('/<project>/upload', methods=['GET', 'POST'])
def upload(project):
    if flask.request.method == 'POST':
        file_obj = flask.request.files
        for file in file_obj.values():
            file_location = os.path.join('.', 'projects', project, secure_filename(file.filename))
            if file.mimetype == 'video/quicktime':
                temp_file = os.path.join('.', 'projects', project, secure_filename('temp.MOV'))
                file.save(temp_file)
                ffmpeg.input(temp_file).filter('scale', -1, 1080).output(file_location).overwrite_output().run()
                os.remove(temp_file)
    return flask.render_template('projects/upload.html', project=project)


@projects_view.route('/<project>/video_gallery')
def video_gallery(project):
    videos = sorted([x.split(os.sep)[-1] for x in glob.glob(os.path.join('.', 'projects', project, '*.MOV'))])
    random_int = random.randint(1, 10000000)
    return flask.render_template('projects/video_gallery.html', project=project, videos=videos, random_int=random_int)


@projects_view.route('/<project>/plot')
def plot_log(project):
    log_data = drone_log_data.get_log_data(project)
    plot_script, plot_div = drone_log_data.get_log_plot(log_data)
    return flask.render_template('projects/plot.html', plot_div=plot_div, plot_script=plot_script, project=project)


@projects_view.route('/<project>/download')
def download(project):
    filename = os.path.join('.', 'projects', project, 'annotations.csv')
    annotations = get_all_annotations(project)
    save_annotations_csv(annotations, filename)
    return flask.send_file(filename, as_attachment=True, attachment_filename='annotations.csv')


def save_annotations_csv(annotations, filename):
    with open(filename, 'w') as fp:
        csv_writer = csv.writer(fp, delimiter=',')
        header = ('name', 'length', 'time', 'lat', 'lon', 'east', 'north', 'zone', 'drone height', 'rotation', 'pos')
        csv_writer.writerow(header)
        for annotation in annotations:
            csv_writer.writerow(annotation)


def get_all_annotations(project):
    annotations = []
    reg_files = os.path.join('.', 'projects', project, '*.json')
    files = glob.glob(reg_files)
    for file in files:
        with open(file, 'r') as fp:
            json_data = json.load(fp)
        objects = json_data['objects']
        video_file = file.split(os.sep)[-1][:-5]
        log_file = None  # todo
        drone_used = None  # todo
        if objects:
            for obj in objects:
                if obj['type'] == 'FrameLine':
                    annotation = get_frame_line_data(obj)
                    annotation.extend(video_file, log_file, drone_used)
                else:
                    annotation = None
                annotations.append(annotation)
    return annotations


def get_frame_line_data(obj):
    # todo
    # name
    # length
    # time
    # lat, lon
    # east, north, zone
    # drone height, rotation, pos
    return obj


@projects_view.route('/<project>/remove')
def remove_project(project):
    shutil.rmtree('./projects/' + project)
    return flask.redirect(flask.url_for('projects.index'))
