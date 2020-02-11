import os
import random


class AppConfig:
    SECRET_KEY = os.urandom(24).hex()
    WTF_CSRF_SECRET_KEY = os.urandom(24).hex()
    OBSCURE_SALT = random.randint(0, 9999999999)
    # Dropzone settings
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_MAX_FILE_SIZE = 100000
    DROPZONE_PARALLEL_UPLOADS = 20
    DROPZONE_TIMEOUT = 1800000
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
