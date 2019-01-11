from flask import Flask, send_from_directory
from flask_dropzone import Dropzone
from flask_obscure import Obscure


class AppConfig:
        # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'
    WTF_CSRF_SECRET_KEY = 'a csrf secret key34643643'

    # Dropzone settings
    DROPZONE_UPLOAD_MULTIPLE = True
    DROPZONE_MAX_FILE_SIZE = 10000
    DROPZONE_PARALLEL_UPLOADS = 20
    DROPZONE_TIMEOUT = 1800000
    # Obscure settings
    OBSCURE_SALT = 2076864838


def serve_projects_file(filename):
    return send_from_directory('projects', filename)


app = Flask(__name__)
app.config.from_object(__name__+'.AppConfig')
app.add_url_rule('/projects/<path:filename>', endpoint='projects_folder', view_func=serve_projects_file)
dropzone = Dropzone(app)
obscure = Obscure(app)
