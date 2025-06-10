from __future__ import annotations

import contextlib
import shutil
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from dvm import create_app
from dvm.app_config import TestConfig
from dvm.db_model import db


@pytest.fixture(scope="session", autouse=True)  # type: ignore[misc]
def cleanup() -> Generator[None]:
    yield None
    with contextlib.suppress(Exception):
        shutil.rmtree(TestConfig.data_dir)


@pytest.fixture(scope="session")  # type: ignore[misc]
def app() -> Flask:
    return create_app(testing=True)


@pytest.fixture(scope="module")  # type: ignore[misc]
def database(app: Flask) -> Generator[SQLAlchemy]:
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()
        yield db


@pytest.fixture(scope="session")  # type: ignore[misc]
def client(app: Flask) -> FlaskClient:
    return app.test_client()
