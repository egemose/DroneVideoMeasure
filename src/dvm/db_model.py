from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
