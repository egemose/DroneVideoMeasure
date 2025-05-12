from __future__ import annotations

import contextlib
import json
import logging
import os
import random
import re
import subprocess
from pathlib import Path

import ffmpeg
import flask
from celery.app.task import Task as CeleryTask
from werkzeug.wrappers.response import Response

from dvm.app_config import Project, Task, Video, celery, data_dir, db, get_random_filename
from dvm.helper_functions import get_all_annotations, save_annotations_csv

logger = logging.getLogger("app." + __name__)
video_gallery_view = flask.Blueprint("video_gallery", __name__)


@video_gallery_view.route("/videos/<project_id>/upload", methods=["GET", "POST"])  # type: ignore[misc]
def upload(project_id: int) -> tuple[Response, int] | Response:
    if flask.request.method == "POST":
        for key, file_obj in flask.request.files.items():
            if key.startswith("file"):
                video_file = os.path.join(
                    data_dir,
                    get_random_filename(file_obj.filename.rsplit(".", 1)[0] + ".mp4"),
                )
                video_mime_type = re.compile("video/*")
                if video_mime_type.match(file_obj.mimetype):
                    temp_filename = get_random_filename(file_obj.filename)
                    logger.debug(f"Uploading file: {video_file}")
                    temp_file = os.path.join(data_dir, temp_filename)
                    file_obj.save(temp_file)
                    logger.debug(f"Upload done for file: {video_file}")
                    logger.debug(f"Calling celery to convert file: {temp_filename} and save as {video_file}")
                    video = Video(
                        file=video_file,
                        name=file_obj.filename,
                        project_id=project_id,
                        image=video_file + ".jpg",
                    )
                    db.session.add(video)
                    db.session.commit()
                    task = convert_after_upload_task.apply_async(args=(temp_file, video.file))
                    task_db = Task(
                        task_id=task.id,
                        function="convert_after_upload_task",
                        video_id=video.id,
                    )
                    db.session.add(task_db)
                    db.session.commit()
                    return flask.jsonify({}), 202
    logger.debug("Render upload after a GET request")
    project = Project.query.get_or_404(project_id)
    return flask.render_template("video_gallery/upload.html", project_id=project.id, project_name=project.name)


def get_video_data(
    video_file: Path, location_video_file: Path | None = None
) -> tuple[float, int, tuple[int, int], tuple[float, float] | tuple[None, None]]:
    logger.debug(f"Reading video data for video {video_file}")
    ffprobe_res = ffmpeg.probe(video_file, cmd="ffprobe")
    video_duration = float(ffprobe_res["format"]["duration"])
    video_nb_frames = int(ffprobe_res["streams"][0]["nb_frames"])
    video_size = (
        int(ffprobe_res["streams"][0]["width"]),
        int(ffprobe_res["streams"][0]["height"]),
    )
    try:
        location_string = ffprobe_res["format"]["tags"]["location"]
    except KeyError:
        if location_video_file:
            ffprobe_res = ffmpeg.probe(location_video_file, cmd="ffprobe")
            location_string = ffprobe_res["format"]["tags"]["location"]
        else:
            location_string = None
    video_pos: tuple[float, float] | tuple[None, None] = (None, None)
    if location_string:
        match = re.match(r"([-+]\d+.\d+)([-+]\d+.\d+)([-+]\d+.\d+)", location_string)
        if match:
            video_pos = (float(match.group(1)), float(match.group(2)))
    return video_duration, video_nb_frames, video_size, video_pos


@celery.task(bind=True)  # type: ignore[misc]
def convert_after_upload_task(self: CeleryTask, temp_path: Path, video_path: Path) -> None:
    self.update_state(state="PROCESSING")
    cmd = [
        "ffmpeg",
        "-i",
        rf"{temp_path}",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-an",
        "-loglevel",
        "24",
        "-movflags",
        "+faststart",
        "-y",
        rf"{video_path}",
    ]
    subprocess.run(cmd, capture_output=True)
    os.remove(temp_path)
    cmd = [
        "ffmpeg",
        "-i",
        rf"{video_path}",
        "-vframes",
        "1",
        "-an",
        "-s",
        "300x200",
        "-ss",
        "0",
        rf"{video_path}.jpg",
    ]
    subprocess.run(cmd, capture_output=True)


@celery.task(bind=True)  # type: ignore[misc]
def concat_videos_task(self: CeleryTask, videos: list[str], output_file: Path) -> None:
    self.update_state(state="PROCESSING")
    video_str = ""
    for video in videos:
        video_str += "file " + video + "\n"
    concat_file = os.path.join(data_dir, "concat.txt")
    with open(concat_file, "w") as file:
        file.write(video_str)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        rf"{concat_file}",
        "-c",
        "copy",
        rf"{output_file}",
    ]
    subprocess.run(cmd, capture_output=True)
    cmd = [
        "ffmpeg",
        "-i",
        rf"{output_file}",
        "-vframes",
        "1",
        "-an",
        "-s",
        "300x200",
        "-ss",
        "0",
        rf"{output_file}.jpg",
    ]
    subprocess.run(cmd, capture_output=True)


def remove_file(file: Path) -> None:
    if file:
        with contextlib.suppress(FileNotFoundError):
            os.remove(file)


@video_gallery_view.route("/videos/status/<task_id>")  # type: ignore[misc]
def task_status(task_id: int) -> Response:
    task_db = Task.query.get_or_404(task_id)
    task = eval(task_db.function + '.AsyncResult("' + task_db.task_id + '")')
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Pending"}
    elif task.state == "SUCCESS":
        response = {"state": task.state, "status": "Done"}
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
    elif task.state != "FAILURE":
        response = {"state": task.state, "status": "Processing"}
    else:
        response = {"state": task.state, "status": str(task.info)}
        video_db = Video.query.get_or_404(task_db.video_id)
        video_db.task_error = str(task.info)
        db.session.delete(task_db)
        db.session.commit()
    return flask.jsonify(response)


@video_gallery_view.route("/videos/<project_id>/video_gallery")  # type: ignore[misc]
def video_gallery(project_id: int) -> Response:
    videos = Video.query.filter_by(project_id=project_id).all()
    random_int = random.randint(1, 10000000)
    logger.debug(f"Render video_gallery for {project_id}")
    return flask.render_template(
        "video_gallery/video_gallery.html",
        project_id=project_id,
        videos=videos,
        random_int=random_int,
    )


@video_gallery_view.route("/videos/<project_id>/concatenate_videos")  # type: ignore[misc]
def concat_videos(project_id: int) -> Response:
    videos = Video.query.filter_by(project_id=project_id).all()
    logger.debug(f"Render concat_videos for {project_id}")
    return flask.render_template("video_gallery/concat_videos.html", project_id=project_id, videos=videos)


@video_gallery_view.route("/videos/<project_id>/concatenating", methods=["POST"])  # type: ignore[misc]
def do_concat_videos(project_id: int) -> tuple[Response, int]:
    videos_json = flask.request.form["videos"]
    output_file_name = flask.request.form["output_name"]
    if output_file_name[-4:] != ".mp4":
        output_file_name += ".mp4"
    video_ids = json.loads(videos_json)
    videos = [Video.query.get_or_404(i) for i in video_ids]
    video_files = [v.file for v in videos]
    logger.debug("Calling celery task for concat")
    video_file = os.path.join(data_dir, get_random_filename(output_file_name))
    video = Video(
        file=video_file,
        name=output_file_name,
        project_id=project_id,
        image=video_file + ".jpg",
    )
    db.session.add(video)
    db.session.commit()
    task = concat_videos_task.apply_async(args=(video_files, video_file))
    task_db = Task(task_id=task.id, function="concat_videos_task", video_id=video.id)
    db.session.add(task_db)
    db.session.commit()
    return flask.jsonify({}), 202


@video_gallery_view.route("/videos/<video_id>/download")  # type: ignore[misc]
def download(video_id: int) -> Response:
    with open("version.txt") as version_file:
        pro_version = version_file.read()
        pro_version = pro_version.strip()
    video = Video.query.get_or_404(video_id)
    project = Project.query.get_or_404(video.project_id)
    annotations = get_all_annotations(project, pro_version, video)
    filename = os.path.join(data_dir, "annotations.csv")
    save_annotations_csv(annotations, filename)
    logger.debug("Sending annotations.csv to user.")
    annotated_filename = f"annotations - {project.name} - {video.name}.csv"
    return flask.send_file(filename, as_attachment=True, download_name=annotated_filename)


@video_gallery_view.route("/videos/<video_id>/remove")  # type: ignore[misc]
def remove_video(video_id: int) -> Response:
    logger.debug(f"Removing video {video_id}")
    video = Video.query.get_or_404(video_id)
    project_id = video.project_id
    remove_file(video.file)
    remove_file(video.image)
    db.session.delete(video)
    db.session.commit()
    return flask.redirect(flask.url_for("video_gallery.video_gallery", project_id=project_id))
