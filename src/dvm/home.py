from __future__ import annotations

import logging
from pathlib import Path
from zipfile import ZipFile

import flask
from werkzeug.wrappers.response import Response

import dvm
from dvm.app_config import data_dir
from dvm.db_model import Drone, Project

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
    logger.debug("Render version")
    return flask.render_template("version.html", version=dvm.__version__)


@home_view.route("/download_logs")  # type: ignore[misc]
def download_logs() -> Response:
    logger.debug("Downloading logs")
    log_dir = data_dir / "logs"
    file_paths = get_all_file_paths(log_dir)
    log_zip = data_dir / "logs.zip"
    with ZipFile(log_zip, "w") as zip_file:
        for file in file_paths:
            zip_file.write(file)
    return flask.send_file(log_zip, as_attachment=True, download_name="logs.zip")


def get_all_file_paths(directory: Path) -> list[Path]:
    file_paths = []
    for root, _, files in Path.walk(directory):
        for filename in files:
            filepath = root / filename
            file_paths.append(filepath)
    return file_paths
