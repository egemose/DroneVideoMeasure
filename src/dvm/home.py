from __future__ import annotations

import logging
import os
from zipfile import ZipFile

import flask
from werkzeug.wrappers.response import Response

from dvm.app_config import Drone, Project, data_dir

logger = logging.getLogger("app." + __name__)
home_view = flask.Blueprint("home", __name__)


@home_view.route("/", methods=["GET", "POST"])  # type: ignore[misc]
def index() -> Response:
    logger.debug("Render index")
    projects = Project.query.all()
    drones = Drone.query.all()
    return flask.render_template("index.html", projects=projects, drones=drones)


@home_view.route("/version")  # type: ignore[misc]
def version() -> Response:
    with open("version.txt") as version_file:
        ver = version_file.read()
    logger.debug("Render version")
    return flask.render_template("version.html", version=ver)


@home_view.route("/download_logs")  # type: ignore[misc]
def download_logs() -> Response:
    logger.debug("Downloading logs")
    log_dir = os.path.join(data_dir, "logs")
    file_paths = get_all_file_paths(log_dir)
    log_zip = os.path.join(data_dir, "logs.zip")
    with ZipFile(log_zip, "w") as zip_file:
        for file in file_paths:
            zip_file.write(file)
    return flask.send_file(log_zip, as_attachment=True, download_name="logs.zip")


def get_all_file_paths(directory: str) -> list[str]:
    file_paths = []
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths
