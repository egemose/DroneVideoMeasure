from __future__ import annotations

import contextlib
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

import flask
import numpy as np
from celery import Task as CeleryTask
from celery import shared_task
from werkzeug.utils import secure_filename
from werkzeug.wrappers.response import Response

from dvm.app_config import Drone, Project, Task, TaskFailure, celery, data_dir, db
from dvm.calibration.calibration import CalibrateCamera
from dvm.forms import EditDroneForm, NewDroneForm

logger = logging.getLogger("app." + __name__)
drones_view = flask.Blueprint("drones", __name__)


@drones_view.route("/drones", methods=["GET", "POST"])  # type: ignore[misc]
def drones() -> str | Response:
    res, drone_form = get_new_drone_form()
    if res:
        return res
    edit_drone_form = get_edit_drone_form()
    drones = Drone.query.all()
    logger.debug("Render drone index")
    return flask.render_template(
        "drones/drones.html",
        drones=drones,
        new_drone_form=drone_form,
        edit_drone_form=edit_drone_form,
    )


def get_new_drone_form() -> tuple[Response | None, NewDroneForm]:
    drones = Drone.query.all()
    form = NewDroneForm()
    if form.validate_on_submit():
        drone_name = form.name.data
        camera_settings = form.camera_settings.data
        if drone_name in [x.name for x in drones]:
            flask.flash("A drone with that name already exist!")
        else:
            drone = Drone(name=drone_name, description=camera_settings)
            db.session.add(drone)
            db.session.commit()
            return flask.redirect(flask.url_for("drones.add_calibration", drone_id=drone.id)), form
    return None, form


def get_edit_drone_form() -> EditDroneForm:
    drones = Drone.query.all()
    form = EditDroneForm()
    if form.validate_on_submit():
        drone_id = form.edit_drone_id.data
        drone_name_before = form.edit_drone_before.data
        new_drone_name = form.edit_name.data
        new_camera_settings = form.edit_camera_settings.data
        drone = Drone.query.get_or_404(drone_id)
        if drone.name in [x.name for x in drones] and drone.name != drone_name_before:
            flask.flash("A drone with that name already exist!")
        else:
            drone.name = new_drone_name
            drone.description = new_camera_settings
            drone.last_update = datetime.now().isoformat(timespec="minutes")
            db.session.commit()
    return form


@drones_view.route("/drones/<drone_id>/calibrate", methods=["GET", "POST"])  # type: ignore[misc]
def add_calibration(drone_id: int) -> Response:
    logger.debug("add_calibration")
    calibration_folder = data_dir / "calibration"
    if not Path.exists(calibration_folder):
        logger.debug("Creating calibration folder")
        Path.mkdir(calibration_folder)
    if flask.request.method == "GET" and Path.is_dir(calibration_folder):
        logger.debug("Removing calibration folder")
        shutil.rmtree(calibration_folder)
        logger.debug("Creating calibration folder")
        Path.mkdir(calibration_folder)
    if flask.request.method == "POST":
        file_obj = flask.request.files
        for file in file_obj.values():
            file_location = calibration_folder / secure_filename(file.filename)
            image_mimetype = re.compile("image/*")
            video_mimetype = re.compile("video/*")
            if image_mimetype.match(file.mimetype) or video_mimetype.match(file.mimetype):
                file.save(file_location)
                logger.debug(f"Saving file: {file_location}")
    logger.debug(f"Render drone calibration for {flask.request.method} request")
    return flask.render_template("drones/calibration.html", drone=drone_id)


@drones_view.route("/dones/<drone_id>/do_calibration", methods=["POST"])  # type: ignore[misc]
def do_calibration(drone_id: int) -> str:
    logger.debug(f"do_calibration is called for drone {drone_id}")
    drone = Drone.query.get_or_404(drone_id)
    drone.calibration = None
    drone.task_error = None
    db.session.commit()
    task = calibration_task.apply_async(args=(drone.id,))
    task_db = Task(task_id=task.id, function="calibration_task", drone_id=drone.id)
    db.session.add(task_db)
    db.session.commit()
    return ""


@shared_task(bind=True)  # type: ignore[misc]
def calibration_task(self: CeleryTask, drone_id: int) -> None:
    self.update_state(state="PROCESSING")
    in_folder = data_dir / "calibration"
    in_folder_temp = data_dir / "calibrationtemp"
    with contextlib.suppress(Exception):
        shutil.rmtree(in_folder_temp)
    Path.mkdir(in_folder_temp)
    calibrate_cam = CalibrateCamera()
    try:
        result = calibrate_cam(in_folder)
        logger.debug(f"calibration result {result}")
        if result == -1:
            shutil.rmtree(in_folder)
            Path.mkdir(in_folder)
            raise Exception("Error: Could not find any checkerboards in the images/video. Try with a new video.")
        if not result:
            shutil.rmtree(in_folder)
            Path.mkdir(in_folder)
            raise Exception("Error: No video or images found. Please try again.")
        drone_db = Drone.query.get(drone_id)
        drone_db.calibration = result
        db.session.commit()
        shutil.rmtree(in_folder)
        Path.mkdir(in_folder)
    except AttributeError as exc:
        shutil.rmtree(in_folder)
        Path.mkdir(in_folder)
        raise Exception("Error: Loading video or images failed. Please try again.") from exc


@drones_view.route("/drones/status/<task_id>")  # type: ignore[misc]
def task_status(task_id: int) -> Response:
    task_db = Task.query.get_or_404(task_id)
    task = eval(task_db.function + '.AsyncResult("' + task_db.task_id + '")')
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Pending"}
    elif task.state == "SUCCESS":
        response = {"state": task.state, "status": "Done"}
        db.session.delete(task_db)
        db.session.commit()
    elif task.state != "FAILURE":
        response = {"state": task.state, "status": "Processing"}
    else:
        response = {"state": task.state, "status": str(task.info)}
        drone = Drone.query.get_or_404(task_db.drone_id)
        drone.task_error = str(task.info)
        db.session.delete(task_db)
        db.session.commit()
    return flask.jsonify(response)


@drones_view.route("/drones/<drone_id>/view_calibration")  # type: ignore[misc]
def view_calibration(drone_id: int) -> Response:
    drone = Drone.query.get_or_404(drone_id)
    try:
        # From 2025-03-31 Five values are stored in
        # drone.calibration, earlier it was only four.
        # This try catch block is to support both cases.
        mtx, dist, fov_x, fov_y, n_images = drone.calibration
    except ValueError:
        mtx, dist, fov_x, fov_y = drone.calibration
        n_images = -1

    logger.debug("Render view_calibration")
    return flask.render_template(
        "drones/view_calibration.html",
        mtx=np.around(mtx, 1),
        dist=np.around(dist, 5),
        fov_x=np.round(fov_x, 2),
        fov_y=np.round(fov_y, 2),
        n_images=n_images,
    )


@drones_view.route("/drones/<drone_id>/remove")  # type: ignore[misc]
def remove_drone(drone_id: int) -> Response:
    logger.debug(f"Removing drone {drone_id}")
    drone = Drone.query.get_or_404(drone_id)
    if drone.task:
        task_db = Task.query.get_or_404(drone.task.id)
        task = eval(task_db.function + '.AsyncResult("' + task_db.task_id + '")')
        task.revoke(terminate=True)
        db.session.delete(task_db)
    for project in drone.projects:
        project_db = Project.query.get_or_404(project.id)
        remove_file(project_db.log_file)
        for video in project_db.videos:
            remove_file(video.file)
            remove_file(video.image)
            db.session.delete(video)
        db.session.delete(project_db)
    db.session.delete(drone)
    db.session.commit()
    return flask.redirect(flask.url_for("drones.drones"))


def remove_file(file: Path) -> None:
    Path.unlink(file, missing_ok=True)
