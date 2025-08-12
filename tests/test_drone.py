from __future__ import annotations

from typing import Any

import pytest
from celery import Task as CeleryTask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from dvm.db_model import Drone, Task
from dvm.drone.drones import calibration_task
from dvm.forms import EditDroneForm, NewDroneForm


def test_drone_page(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/drones")
    assert response.status_code == 200
    assert b"Add Drone" in response.data


def test_add_new_drone_form(client: FlaskClient, database: SQLAlchemy) -> None:
    drone_form = NewDroneForm(formdata=None, name="Test-Drone-42", camera_settings="Test-Cam")
    response = client.post("/drones", data=drone_form.data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Upload images/video with a checkerboard" in response.data
    drone = Drone.query.all()[0]
    assert drone.name == "Test-Drone-42"
    assert drone.description == "Test-Cam"
    response = client.post("/drones", data=drone_form.data, follow_redirects=True)
    assert b"A drone with that name already exist!" in response.data


def test_edit_drone_form(client: FlaskClient, database: SQLAlchemy) -> None:
    drone = Drone.query.all()[0]
    assert drone.id == 1
    drone_form = EditDroneForm(
        formdata=None,
        edit_drone_id=1,
        edit_drone_before="Test-Drone-42",
        edit_name="Test-Drone-43",
        edit_camera_settings="Test Cam Settings",
    )
    response = client.post("/drones", data=drone_form.data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test-Drone-43" in response.data
    assert b"Test Cam Settings" in response.data


def test_add_calibration(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/drones/1/calibrate")
    assert response.status_code == 200
    assert b"Upload images/video with a checkerboard" in response.data


def test_do_calibration(client: FlaskClient, database: SQLAlchemy, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockTask:
        id = 1

    def mock_apply_async(*args: Any, **kwargs: Any) -> MockTask:
        return MockTask()

    with monkeypatch.context() as mp:
        mp.setattr(calibration_task, "apply_async", mock_apply_async)
        response = client.post("/drones/1/do_calibration", data={"coverage": 15, "n_images": 30})
    assert response.status_code == 302
    task = Task.query.all()[0]
    assert task.id == 1


def test_task_status(client: FlaskClient, database: SQLAlchemy, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockTask:
        state = "SUCCESS"

    def mock_AsyncResult(*args: Any, **kwargs: Any) -> MockTask:
        return MockTask()

    with monkeypatch.context() as mp:
        mp.setattr(CeleryTask, "AsyncResult", mock_AsyncResult)
        response = client.get("/drones/status/1")
    assert response.status_code == 200
    assert response.json["state"] == "SUCCESS"
    tasks = Task.query.all()
    assert not tasks


def test_remove_drone(client: FlaskClient, database: SQLAlchemy) -> None:
    response = client.get("/drones/1/remove", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test-Drone-42" not in response.data
    assert b"Test-Drone-43" not in response.data
    drones = Drone.query.all()
    assert not drones
