from __future__ import annotations

import secrets
from pathlib import Path

from werkzeug.utils import secure_filename


def get_random_filename(file: str) -> str:
    while True:
        name = secrets.token_urlsafe(8)
        file_type = "." + file.rsplit(".", 1)[-1]
        filename = str(secure_filename(name + file_type))
        return filename


class AppConfig:
    SECRET_KEY = secrets.token_hex(32)
    WTF_CSRF_SECRET_KEY = secrets.token_hex(32)
    OBSCURE_SALT = secrets.randbelow(9999999999)
    DROPZONE_UPLOAD_MULTIPLE = False
    DROPZONE_MAX_FILE_SIZE = 100000
    DROPZONE_PARALLEL_UPLOADS = 1
    DROPZONE_TIMEOUT = 1800000
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = "image/*, video/*, .mov"
    CELERY = {
        "broker_url": "redis://redis:6379/0",
        "result_backend": "redis://redis:6379/0",
    }
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:example@db:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    data_dir = Path("/app_data").resolve()


class TestConfig(AppConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    CELERY = {
        "broker_url": "redis://",
        "result_backend": "redis://",
    }
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    data_dir = Path("./tests/temp").resolve()
