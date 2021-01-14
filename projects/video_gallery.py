
import json
import os
import random
import re
import subprocess
import logging
import flask
import ffmpeg
import numpy as np
import csv
from drone.fov import fov
from drone.drone_log_data import drone_log
from app_config import data_dir, get_random_filename, celery, Task, Project, Video, Drone, db


logger = logging.getLogger('app.' + __name__)
video_gallery_view = flask.Blueprint('video_gallery', __name__)


@video_gallery_view.route('/videos/<project_id>/upload', methods=['GET', 'POST'])
def upload(project_id):
    if flask.request.method == 'POST':
        for key, file in flask.request.files.items():
            if key.startswith('file'):
                video_file = os.path.join(data_dir, get_random_filename(file.filename.rsplit('.', 1)[0] + '.mp4'))
                video_mime_type = re.compile('video/*')
                if video_mime_type.match(file.mimetype):
                    temp_filename = get_random_filename(file.filename)
                    logger.debug(f'Uploading file: {video_file}')
                    temp_file = os.path.join(data_dir, temp_filename)
                    file.save(temp_file)
                    logger.debug(f'Upload done for file: {video_file}')
                    logger.debug(f'Calling celery to convert file: {temp_filename} and save as {video_file}')
                    video = Video(file=video_file, name=file.filename, project_id=project_id, image=video_file + '.jpg')
                    db.session.add(video)
                    db.session.commit()
                    task = convert_after_upload_task.apply_async(args=(temp_file, video.file))
                    task_db = Task(task_id=task.id, function='convert_after_upload_task', video_id=video.id)
                    db.session.add(task_db)
                    db.session.commit()
                    return flask.jsonify({}), 202
    logger.debug(f'Render upload after a GET request')
    project = Project.query.get_or_404(project_id)
    return flask.render_template('video_gallery/upload.html', project_id=project.id, project_name=project.name)


def get_video_data(video_file, location_video_file=None):
    logger.debug(f'Reading video data for video {video_file}')
    ffprobe_res = ffmpeg.probe(video_file, cmd='ffprobe')
    video_duration = float(ffprobe_res['format']['duration'])
    video_nb_frames = int(ffprobe_res['streams'][0]['nb_frames'])
    video_size = (int(ffprobe_res['streams'][0]['width']), int(ffprobe_res['streams'][0]['height']))
    try:
        location_string = ffprobe_res['format']['tags']['location']
    except KeyError:
        if location_video_file:
            ffprobe_res = ffmpeg.probe(location_video_file, cmd='ffprobe')
            location_string = ffprobe_res['format']['tags']['location']
        else:
            location_string = None
    video_pos = (None, None)
    if location_string:
        match = re.match(r'([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)', location_string)
        if match:
            video_pos = (float(match.group(1)), float(match.group(2)))
    return video_duration, video_nb_frames, video_size, video_pos


@celery.task(bind=True)
def convert_after_upload_task(self, temp_path, video_path):
    self.update_state(state='PROCESSING')
    cmd = ['ffmpeg', '-i', r'{}'.format(temp_path), '-preset', 'ultrafast', '-tune', 'zerolatency', '-an', '-loglevel', '24', '-movflags', '+faststart', '-y', r'{}'.format(video_path)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.remove(temp_path)
    cmd = ['ffmpeg', '-i', r'{}'.format(video_path), '-vframes', '1', '-an', '-s', '300x200', '-ss', '0', r'{}.jpg'.format(video_path)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@celery.task(bind=True)
def concat_videos_task(self, videos, output_file):
    self.update_state(state='PROCESSING')
    video_str = ''
    for video in videos:
        video_str += 'file ' + video + '\n'
    concat_file = os.path.join(data_dir, 'concat.txt')
    with open(concat_file, 'w') as file:
        file.write(video_str)
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', r'{}'.format(concat_file), '-c', 'copy', r'{}'.format(output_file)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd = ['ffmpeg', '-i', r'{}'.format(output_file), '-vframes', '1', '-an', '-s', '300x200', '-ss', '0', r'{}.jpg'.format(output_file)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def remove_file(file):
    if file:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass


@video_gallery_view.route('/videos/status/<task_id>')
def task_status(task_id):
    task_db = Task.query.get_or_404(task_id)
    task = eval(task_db.function + '.AsyncResult("' + task_db.task_id + '")')
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'status': 'Done'}
        video_db = Video.query.get_or_404(task_db.video_id)
        video_data = get_video_data(video_db.file)
        video_db.duration = video_data[0]
        video_db.frames = video_data[1]
        video_db.width = video_data[2][0]
        video_db.height = video_data[2][1]
        video_db.latitude = video_data[3][0]
        video_db.longitude = video_data[3][1]
        db.session.delete(task_db)
        db.session.commit()
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'status': 'Processing'}
    else:
        response = {'state': task.state, 'status': str(task.info)}
        video_db = Video.query.get_or_404(task_db.video_id)
        video_db.task_error = str(task.info)
        db.session.delete(task_db)
        db.session.commit()
    return flask.jsonify(response)


@video_gallery_view.route('/videos/<project_id>/video_gallery')
def video_gallery(project_id):
    videos = Video.query.filter_by(project_id=project_id).all()
    random_int = random.randint(1, 10000000)
    logger.debug(f'Render video_gallery for {project_id}')
    return flask.render_template('video_gallery/video_gallery.html', project_id=project_id, videos=videos, random_int=random_int)


@video_gallery_view.route('/videos/<project_id>/concatenate_videos')
def concat_videos(project_id):
    videos = Video.query.filter_by(project_id=project_id).all()
    logger.debug(f'Render concat_videos for {project_id}')
    return flask.render_template('video_gallery/concat_videos.html', project_id=project_id, videos=videos)


@video_gallery_view.route('/videos/<project_id>/concatenating', methods=['POST'])
def do_concat_videos(project_id):
    videos_json = flask.request.form.get('videos')
    output_file_name = flask.request.form.get('output_name')
    if output_file_name[-4:] != '.mp4':
        output_file_name += '.mp4'
    video_ids = json.loads(videos_json)
    videos = [Video.query.get_or_404(i) for i in video_ids]
    video_files = [v.file for v in videos]
    logger.debug(f'Calling celery task for concat')
    video_file = os.path.join(data_dir, get_random_filename(output_file_name))
    video = Video(file=video_file, name=output_file_name, project_id=project_id, image=video_file + '.jpg')
    db.session.add(video)
    db.session.commit()
    task = concat_videos_task.apply_async(args=(video_files, video_file))
    task_db = Task(task_id=task.id, function='concat_videos_task', video_id=video.id)
    db.session.add(task_db)
    db.session.commit()
    return flask.jsonify({}), 202


@video_gallery_view.route('/videos/<video_id>/download')
def download(video_id):
    with open('version.txt') as version_file:
        pro_version = version_file.read()
    video = Video.query.get_or_404(video_id)
    annotations = get_annotations(video, pro_version)
    filename = os.path.join(data_dir, 'annotations.csv')
    save_annotations_csv(annotations, filename)
    logger.debug(f'Sending annotations.csv to user.')
    return flask.send_file(filename, as_attachment=True, attachment_filename='annotations.csv')


def get_annotations(video, pro_version):
    logger.debug(f'Getting all annotations')
    annotations = []
    project = Project.query.get_or_404(video.project_id)
    drone = Drone.query.get_or_404(project.drone_id)
    fov.set_camera_params(*drone.calibration)
    drone_log.get_log_data(project.log_file)
    json_data = json.loads(video.json_data)
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
        direction = (obj.get('x1') < 0 and obj.get('y1') < 0) or (obj.get('x2') < 0 and obj.get('y2') < 0)
        if direction:
            image_point1 = (obj.get('left'), obj.get('top'))
            image_point2 = (obj.get('left') + obj.get('width'), obj.get('top') + obj.get('height'))
        else:
            image_point1 = (obj.get('left') + obj.get('width'), obj.get('top'))
            image_point2 = (obj.get('left'), obj.get('top') + obj.get('height'))
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


@video_gallery_view.route('/videos/<video_id>/remove')
def remove_video(video_id):
    logger.debug(f'Removing video {video_id}')
    video = Video.query.get_or_404(video_id)
    project_id = video.project_id
    remove_file(video.file)
    remove_file(video.image)
    db.session.delete(video)
    db.session.commit()
    return flask.redirect(flask.url_for('video_gallery.video_gallery', project_id=project_id))
