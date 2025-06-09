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
