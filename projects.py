import csv
import glob
import os
import shutil
import random
import subprocess
import time
from collections import namedtuple
import ffmpeg
import flask
import json
from werkzeug.utils import secure_filename
from forms import NewProjectForm, EditProjectForm
from markings import MarkingView
import drone_log_data

# todo add warning when clear Annotations
# todo check if enter is hit what happens
# todo add way to add drones and select them
# todo maybe rethink new project form

marking_class = MarkingView()

project_tuple = namedtuple('project', ['title', 'description', 'last_updated'])


projects_view = flask.Blueprint('projects', __name__)


@projects_view.route('/version')
def version():
    with open('version.txt') as version_file:
            ver = version_file.read()
    return flask.render_template('projects/version.html', version=ver)


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
        last_modified_string = get_last_modified_time(project_title)
        with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'r') as file:
            description = flask.Markup(file.read())
        project = project_tuple(project_title, description, last_modified_string)
        project_dict.update({project_title: project})
    return project_dict


def get_last_modified_time(project):
    all_files = glob.glob(os.path.join('.', 'projects', project, '*'))
    last_m_time = 0
    m_time = 0
    for file in all_files:
        m_time = os.path.getmtime(file)
        if last_m_time < m_time:
            last_m_time = m_time
    current_time = time.time()
    time_past = round(current_time - m_time)
    last_modified_string = get_last_updated_time_as_string(time_past)
    return last_modified_string


def get_new_project_form(project_dict):
    form = NewProjectForm()
    if form.validate_on_submit():
        description = form.description.data
        project_title = form.name.data
        if project_title in project_dict:
            flask.flash('A project with that name already exist!')
        else:
            os.mkdir(os.path.join('.', 'projects', project_title))
            with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'w') as file:
                file.write(description)
            return flask.redirect(flask.url_for('projects.upload', project=project_title)), form
    return None, form


def get_edit_project_form(project_dict):
    form = EditProjectForm()
    if form.validate_on_submit():
        project_before = form.edit_project_before.data
        description = form.edit_description.data
        project_title = form.edit_name.data
        if project_title in project_dict and not project_title == project_before:
            flask.flash('A project with that name already exist!')
        else:
            project_dict.pop(project_before, None)
            os.rename(os.path.join('.', 'projects', project_before), os.path.join('.', 'projects', project_title))
            with open(os.path.join('.', 'projects', project_title, 'description.txt'), 'w') as file:
                file.write(description)
            last_updated = get_last_updated_time_as_string(0)
            project = project_tuple(project_title, description, last_updated)
            project_dict.update({project_title: project})
    return form


def get_last_updated_time_as_string(time_in):
    d = time_in // (60 * 60 * 24)
    h = (time_in - d * 60 * 60 * 24) // (60 * 60)
    m = (time_in - d * 60 * 60 * 24 - h * 60 * 60) // 60
    if d == 0:
        d_string = ''
    elif d == 1:
        d_string = f' {d} day'
    else:
        d_string = f' {d} days'
    if h == 0 and d == 0:
        h_string = ''
    elif h == 1:
        h_string = f' {h} hr'
    else:
        h_string = f' {h} hrs'
    if m == 1:
        m_string = f' {m} min ago'
    else:
        m_string = f' {m} mins ago'
    last_modified_string = 'Last updated' + d_string + h_string + m_string
    return last_modified_string


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
            elif file.mimetype == 'text/plain':
                file.save(file_location)
                converted_log = os.path.join('.', 'projects', project, 'drone_log.csv')
                cmd = 'wine drone_log/TXTlogToCSVtool "' + file_location + '" "' + converted_log + '"'
                subprocess.call(cmd, shell=True)
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


@projects_view.route('/<project>/<video_file>/annotate')
def video(project, video_file):
    log_data = drone_log_data.get_log_data(project)
    video_duration, video_frames, video_size, video_pos = drone_log_data.get_video_data(project, video_file)
    video_start_time = drone_log_data.match_log_and_video(log_data, video_duration, video_pos)
    plot_script, plot_div = drone_log_data.get_log_plot_with_video(log_data, video_start_time, video_duration, video_frames)
    json_filename = os.path.join('.', 'projects', project, video_file + '.json')
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
                video_width=video_size[0],
                video_height=video_size[1],
                num_frames=video_frames,
                fps=video_frames / video_duration)
    return flask.render_template('projects/video.html', **args)


@projects_view.route('/<project>/<video_file>/save', methods=['POST'])
def save_fabric_json(project, video_file):
    json_data = json.loads(flask.request.form.get('fabric_json'))
    file_name = os.path.join('.', 'projects', project, video_file + '.json')
    with open(file_name, 'w') as json_file:
        json.dump(json_data, json_file)
    return ''


@projects_view.route('/add_marking', methods=['POST'])
def add_marking():
    global marking_class
    add_name = flask.request.form.get('add_name')
    if add_name == 'true':
        name = flask.request.form.get('name')
        marking_class.add_name(name)
    else:
        fabric_json = flask.request.form.get('fabric_json')
        marking_class = MarkingView.from_fabric_json(fabric_json)
    return flask.jsonify(marking_class.get_data())
