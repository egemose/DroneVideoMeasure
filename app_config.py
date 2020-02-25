import os
import random
from celery import Celery
from flask_dropzone import Dropzone
from flask_obscure import Obscure
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


class AppConfig:
    SECRET_KEY = os.urandom(24).hex()
    WTF_CSRF_SECRET_KEY = os.urandom(24).hex()
    OBSCURE_SALT = random.randint(0, 9999999999)
    # Dropzone settings
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_MAX_FILE_SIZE = 100000
    DROPZONE_PARALLEL_UPLOADS = 1
    DROPZONE_TIMEOUT = 1800000
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:example@db:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


base_dir = os.path.abspath('data')

celery = Celery(__name__, broker=AppConfig.CELERY_BROKER_URL, backend=AppConfig.CELERY_RESULT_BACKEND)
tasks = {}

dropzone = Dropzone()
obscure = Obscure()
db = SQLAlchemy()
migrate = Migrate()
