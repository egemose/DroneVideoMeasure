from __future__ import annotations

from pathlib import Path

import numpy as np
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.file import FileStorage

from dvm.db_model import Drone, Project, db
from dvm.forms import EditProjectForm, NewDroneForm, NewProjectForm


def test_empty_project_page(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert b"Add Project" in response.data
    assert b"fa-exclamation-triangle" in response.data
    # add drone to enable adding projects
    drone_form = NewDroneForm(formdata=None, name="Test-Drone-for-Project")
    response = client.post("/drones", data=drone_form.data, follow_redirects=True)
    assert response.status_code == 200
    mtx = np.array([[2850, 0, 2043], [0, 2852, 1082], [0, 0, 1]])
    dist = np.array([0.01918, -0.06466, -0.00013, 0.00027, 0.07863])
    fov_x = 71.4
    fox_y = 41.48
    n_images_used = 31
    drone_db = db.get_or_404(Drone, 1)
    drone_db.calibration = (mtx, dist, fov_x, fox_y, n_images_used)
    db.session.commit()
    response = client.post("/projects")
    assert response.status_code == 200
    assert b"Add Project" in response.data
    assert b"fa-exclamation-triangle" not in response.data


def test_add_project_form(client: FlaskClient, database: SQLAlchemy) -> None:
    drone = Drone.query.all()[0]
    log_file = Path("./tests/test_data/test_drone_log.csv").resolve()
    with log_file.open("br") as file:
        project_form = NewProjectForm(
            formdata=None,
            name="Test-Project-12",
            description="Test Project number 12",
            drone=drone.id,
            log_file=FileStorage(stream=file, filename=log_file),
        )
        response = client.post("/projects", data=project_form.data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test-Project-12" in response.data
    assert b"Test Project number 12" in response.data
    assert b"fa-exclamation-triangle" not in response.data


def test_edit_project_form(client: FlaskClient, database: SQLAlchemy) -> None:
    project = Project.query.all()[0]
    drone = Drone.query.all()[0]
    project_form = EditProjectForm(
        formdata=None,
        edit_project_id=project.id,
        edit_name="Test-Project-11",
        edit_project_before="Test-Project-12",
        edit_drone=drone.id,
    )
    response = client.post("/projects", data=project_form.data)
    assert response.status_code == 200
    assert b"Test-Project-11" in response.data


def test_project_plot(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/projects/1/plot")
    assert response.status_code == 200
    assert b"Drone flight path" in response.data


def test_project_download(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/projects/1/download")
    assert response.status_code == 200
    assert b"name,time,frame" in response.data


def test_remove_project(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/projects/1/remove", follow_redirects=True)
    assert response.status_code == 200
    assert not Project.query.all()
