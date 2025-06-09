from __future__ import annotations

import logging
import random
from pathlib import Path

import flask
from werkzeug.wrappers.response import Response

import dvm
from dvm.app_config import data_dir, get_random_filename
from dvm.db_model import Drone, Project, db
from dvm.drone import plot_log_data
from dvm.drone.drone_log_data import drone_log
from dvm.forms import EditProjectForm, NewProjectForm
from dvm.helper_functions import get_all_annotations, save_annotations_csv

logger = logging.getLogger("app." + __name__)
projects_view = flask.Blueprint("projects", __name__)


@projects_view.route("/projects", methods=["GET", "POST"])  # type: ignore[misc]
def projects() -> str | Response:
    random_int = random.randint(1, 10000000)
    res, new_project_form = get_new_project_form()
    if res:
        return res
    edit_project_form = get_edit_project_form()
    projects = Project.query.all()
    drones = Drone.query.all()
    drones = [(x.id, x.name) for x in drones if x.calibration]
    arguments = {
        "projects": projects,
        "drones": drones,
        "random_int": random_int,
        "new_project_form": new_project_form,
        "edit_project_form": edit_project_form,
    }
    logger.debug("Render index")
    return flask.render_template("projects/projects.html", **arguments)


def get_new_project_form() -> tuple[Response | None, NewProjectForm]:
    form = NewProjectForm()
    drones = Drone.query.all()
    form.drone.choices = [(x.id, x.name) for x in drones if x.calibration]
    if form.validate_on_submit():
        project_title = form.name.data
        description = form.description.data
        drone_id = form.drone.data
        projects = Project.query.all()
        if project_title in [x.name for x in projects]:
            flask.flash("A project with that name already exist!")
        else:
            logger.debug(f"Creating project with name {project_title}")
            log_file = None
            if form.log_file.data:
                log_error = None
                log_filename = get_random_filename(form.log_file.data.filename)
                log_file = data_dir.joinpath(log_filename)
                form.log_file.data.save(log_file)
                success = drone_log.test_log(log_file)
                if not success:
                    remove_file(log_file)
                    log_filename = None  # type: ignore[assignment]
                    log_error = "Error interpreting the drone log file. Try and upload the log file again."
            else:
                log_error = "No drone log file added. Please add a log file."
            project = Project(
                name=project_title,
                description=description,
                drone_id=drone_id,
                log_file=str(log_file),
                log_error=log_error,
            )
            db.session.add(project)
            db.session.commit()
            return flask.redirect(flask.url_for("projects.projects", project_id=project.id)), form
    return None, form


def get_edit_project_form() -> EditProjectForm:
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
        logger.debug(f"Editing project {project_before} with new name {project_title}")
        if project_title in projects and project_title != project_before:
            flask.flash("A project with that name already exist!")
        else:
            project = Project.query.get_or_404(project_id)
            project.name = project_title
            project.description = description
            project.drone_id = drone_id
            if form.edit_log_file.data:
                remove_file(project.log_file)
                log_error = None
                log_filename = get_random_filename(form.edit_log_file.data.filename)
                log_file = data_dir.joinpath(log_filename)
                form.edit_log_file.data.save(log_file)
                success = drone_log.test_log(log_file)
                if success:
                    project.log_file = str(log_file)
                else:
                    remove_file(log_file)
                    project.log_file = None
                    log_error = "Error interpreting the drone log file. Try and upload the log file again."
                project.log_error = log_error
            db.session.commit()
    return form


@projects_view.route("/projects/<project_id>/plot")  # type: ignore[misc]
def plot_log(project_id: int) -> Response:
    project = Project.query.get_or_404(project_id)
    drone_log.get_log_data(Path(project.log_file))
    plot_script, plot_div = plot_log_data.get_log_plot(drone_log.log_data())
    logger.debug(f"Render video plot for {project_id}")
    return flask.render_template(
        "projects/plot.html",
        plot_div=plot_div,
        plot_script=plot_script,
        project_id=project_id,
        drone_path=drone_log.pos,
    )


@projects_view.route("/projects/<project_id>/download")  # type: ignore[misc]
def download(project_id: int) -> Response:
    project = Project.query.get_or_404(project_id)
    annotations = get_all_annotations(project, dvm.__version__)
    filename = data_dir / "annotations.csv"
    save_annotations_csv(annotations, filename)
    logger.debug("Sending annotations.csv to user.")
    return flask.send_file(filename, as_attachment=True)


@projects_view.route("/projects/<project_id>/remove")  # type: ignore[misc]
def remove_project(project_id: int) -> Response:
    logger.debug(f"Removing project {project_id}")
    project = Project.query.get_or_404(project_id)
    remove_file(project.log_file)
    for video in project.videos:
        remove_file(video.file)
        remove_file(video.image)
        db.session.delete(video)
    db.session.delete(project)
    db.session.commit()
    return flask.redirect(flask.url_for("projects.projects"))


def remove_file(file: Path) -> None:
    Path.unlink(file, missing_ok=True)
