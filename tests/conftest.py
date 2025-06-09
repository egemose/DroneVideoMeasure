from __future__ import annotations

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from dvm import create_app
from dvm.db_model import db


@pytest.fixture(scope="module")  # type: ignore[misc]
def init_database(app: Flask) -> Generator[SQLAlchemy]:
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()
        yield db


@pytest.fixture(scope="session")  # type: ignore[misc]
def app() -> Flask:
    return create_app(testing=True)


@pytest.fixture(scope="session")  # type: ignore[misc]
def client(app: Flask) -> FlaskClient:
    return app.test_client()
