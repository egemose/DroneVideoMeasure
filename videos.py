import os
import json
import flask
from markings import MarkingView
import drone_log_data


marking_class = MarkingView()
videos_view = flask.Blueprint('videos', __name__)


@videos_view.route('/<project>/<video_file>/annotate')
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
        marking_class = MarkingView.from_fabric_json(fabric_json)
    return flask.jsonify(marking_class.get_data())
