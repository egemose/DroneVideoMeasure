from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy


def test_config(app: Flask) -> None:
    assert app.testing


def test_home_page(client: FlaskClient, init_database: SQLAlchemy) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"Drone Video Measure" in response.data
    assert b"Usage" in response.data
    assert b"Supported Drones" in response.data
    assert b"Author" in response.data
    assert b"License" in response.data
    assert b"Henrik Dyrberg Egemose" in response.data
    assert b"SDU UAS Center" in response.data


def test_version_page(client: FlaskClient, init_database: SQLAlchemy) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert b"You are using version" in response.data
