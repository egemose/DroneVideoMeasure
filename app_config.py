import os
import random


class AppConfig:
    SECRET_KEY = os.urandom(24).hex()
    WTF_CSRF_SECRET_KEY = os.urandom(24).hex()
    OBSCURE_SALT = random.randint(0, 9999999999)
