import os
import json
import flask
import csv
from markings import MarkingView
from help_functions import drone_log, fov
import plot_log_data


marking_class = MarkingView(drone_log, fov)
videos_view = flask.Blueprint('videos', __name__)


@videos_view.route('/<project>/plot')
def plot_log(project):
    if drone_log.project != project:
        drone_log.get_log_data(project)
    plot_script, plot_div = plot_log_data.get_log_plot(drone_log.log_data())
    return flask.render_template('videos/plot.html', plot_div=plot_div, plot_script=plot_script, project=project)


@videos_view.route('/<project>/<video_file>/annotate')
def video(project, video_file):
    with open(os.path.join('.', 'projects', project, 'drone.txt')) as file:
        reader = csv.DictReader(file)
        for row in reader:
            fov.set_fov(float(row.get('hfov')), float(row.get('vfov')))
    if drone_log.project != project:
        drone_log.get_log_data(project)
    drone_log.get_video_data(project, video_file)
    fov.set_image_size(*drone_log.video_size)
    video_start_time, message = drone_log.match_log_and_video()
    if message:
        flask.flash(message, 'warning')
    plot_script, plot_div = plot_log_data.get_log_plot_with_video(drone_log.log_data(), video_start_time, drone_log.video_duration, drone_log.video_nb_frames)
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
                video_width=drone_log.video_size[0],
                video_height=drone_log.video_size[1],
                num_frames=drone_log.video_nb_frames,
                fps=drone_log.video_nb_frames / drone_log.video_duration)
    return flask.render_template('videos/video.html', **args)


@videos_view.route('/<project>/<video_file>/save', methods=['POST'])
def save_fabric_json(project, video_file):
    json_data = json.loads(flask.request.form.get('fabric_json'))
    file_name = os.path.join('.', 'projects', project, video_file + '.json')
    with open(file_name, 'w') as json_file:
        json.dump(json_data, json_file)
    return ''


@videos_view.route('/add_marking', methods=['POST'])
def add_marking():
    global marking_class
    add_name = flask.request.form.get('add_name')
    if add_name == 'true':
        name = flask.request.form.get('name')
        marking_class.add_name(name)
    else:
        fabric_json = flask.request.form.get('fabric_json')
        marking_class = MarkingView.from_fabric_json(fabric_json, drone_log, fov)
    return flask.jsonify(marking_class.get_data())
