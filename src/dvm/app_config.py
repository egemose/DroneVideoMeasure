from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from celery import Celery
from flask import Flask
from flask_dropzone import Dropzone
from flask_migrate import Migrate
from flask_obscure import Obscure
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


class TaskFailure(Exception):
    pass


class AppConfig:
    SECRET_KEY = secrets.token_hex(32)
    WTF_CSRF_SECRET_KEY = secrets.token_hex(32)
    OBSCURE_SALT = secrets.randbelow(9999999999)
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_MAX_FILE_SIZE = 100000
    DROPZONE_PARALLEL_UPLOADS = 1
    DROPZONE_TIMEOUT = 1800000
    CELERY_BROKER_URL = "redis://redis:6379/0"
    result_backend = "redis://redis:6379/0"
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:example@db:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


data_dir = Path(os.path.abspath("/app_data"))

celery = Celery(
    __name__,
    broker=AppConfig.CELERY_BROKER_URL,
    backend=AppConfig.result_backend,
)


def make_celery(app: Flask) -> Celery:
    global celery
    celery.conf.update(app.config)
    BaseTask = celery.Task

    class ContextTask(BaseTask):  # type: ignore[valid-type, misc]
        abstract = True

        def __call__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
            with app.app_context():
                return BaseTask.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


dropzone = Dropzone()
obscure = Obscure()
db = SQLAlchemy()
migrate = Migrate(compare_type=True)


def get_random_filename(file: str) -> str:
    while True:
        name = secrets.token_urlsafe(8)
        file_type = "." + file.rsplit(".", 1)[-1]
        filename = str(secure_filename(name + file_type))
        return filename


class Project(db.Model):  # type: ignore[name-defined, misc]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.Text())
    log_file = db.Column(db.String(), nullable=True)
    drone_id = db.Column(db.Integer, db.ForeignKey("drone.id"), nullable=False)
    videos = db.relationship("Video", backref="project", lazy=True)
    log_error = db.Column(db.String(), nullable=True)

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Video(db.Model):  # type: ignore[name-defined, misc]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    file = db.Column(db.String(), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    image = db.Column(db.String())
    duration = db.Column(db.Float)
    frames = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    start_time = db.Column(db.DateTime())
    takeoff_altitude = db.Column(db.Float, default=0.0)
    json_data = db.Column(db.String())
    task = db.relationship("Task", backref="Video", lazy=True, uselist=False)
    task_error = db.Column(db.String(), nullable=True)

    def __repr__(self) -> str:
        return f"<Video {self.file}>"


class Drone(db.Model):  # type: ignore[name-defined, misc]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.Text())
    calibration = db.Column(db.PickleType())
    projects = db.relationship("Project", backref="drone", lazy=True)
    task = db.relationship("Task", backref="Drone", lazy=True, uselist=False)
    task_error = db.Column(db.String(), nullable=True)

    def __repr__(self) -> str:
        return f"<Drone {self.name}>"


class Task(db.Model):  # type: ignore[name-defined, misc]
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(), unique=True, nullable=False)
    function = db.Column(db.String())
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=True)
    drone_id = db.Column(db.Integer, db.ForeignKey("drone.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Task {self.task_id}>"
