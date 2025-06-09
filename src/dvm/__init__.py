from __future__ import annotations

import logging.handlers
import os
from logging import Logger
from pathlib import Path

import werkzeug.exceptions
from celery import Celery, Task
from flask import Flask, Response, render_template, send_from_directory

from dvm.app_config import AppConfig, data_dir, db, dropzone, make_celery, migrate, obscure
from dvm.drone.drones import drones_view
from dvm.home import home_view
from dvm.projects.projects import projects_view
from dvm.projects.video_gallery import video_gallery_view
from dvm.video.videos import videos_view

def setup_logger(testing: bool = False) -> Logger:
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    if not testing:
        log_dir = data_dir / "logs"
        log_file = log_dir / "python.log"
        if not Path.exists(log_dir):
            Path.mkdir(log_dir)
        fh = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=2)
        formatter = logging.Formatter("{asctime} | {name:<20} | {levelname:<8} - {message}", style="{")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        logger.addHandler(logging.NullHandler())
    return logger


def serve_data_file(filename: str) -> Response:
    return send_from_directory(Path("..") / "/app_data", os.path.split(filename)[-1])


def serve_node_modules(filename: str) -> Response:
    return send_from_directory(Path("..") / "/node_modules", filename)


def page_not_found(e: werkzeug.exceptions.NotFound) -> tuple[str, int]:
    return render_template("404.html"), 404


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):  # type: ignore[misc]
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    setup_logger(testing)
    if not testing:
        app.config.from_object(AppConfig)
    else:
        app.config.from_object(TestConfig)
    app.register_error_handler(404, page_not_found)
    app.add_url_rule("/data/<path:filename>", endpoint="data", view_func=serve_data_file)
    app.add_url_rule(
        "/node_modules/<path:filename>",
        endpoint="node_modules",
        view_func=serve_node_modules,
    )
    celery_init_app(app)
    dropzone.init_app(app)
    obscure.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(projects_view)
    app.register_blueprint(videos_view)
    app.register_blueprint(drones_view)
    app.register_blueprint(home_view)
    app.register_blueprint(video_gallery_view)
    return app

# Current version
__version__ = "2.0.2"
