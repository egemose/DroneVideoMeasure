from flask import Flask, send_from_directory
from flask_dropzone import Dropzone
from flask_obscure import Obscure
import argparse
from projects import projects_view
from videos import videos_view
from misc import misc_view
from drones import drones_view
from app_config import AppConfig


def serve_projects_file(filename):
    return send_from_directory('projects', filename)

# AppConfig object holds:
# SECRET_KEY = 'some secret'
# WTF_CSRF_SECRET_KEY = 'csrf secret key'
# OBSCURE_SALT = some random int

# Dropzone settings
AppConfig.DROPZONE_UPLOAD_MULTIPLE = True
AppConfig.DROPZONE_MAX_FILE_SIZE = 100000
AppConfig.DROPZONE_PARALLEL_UPLOADS = 20
AppConfig.DROPZONE_TIMEOUT = 1800000

app = Flask(__name__)
app.config.from_object(AppConfig)
app.add_url_rule('/projects/<path:filename>', endpoint='projects_folder', view_func=serve_projects_file)
dropzone = Dropzone(app)
obscure = Obscure(app)

app.register_blueprint(projects_view)
app.register_blueprint(videos_view)
app.register_blueprint(misc_view)
app.register_blueprint(drones_view)


def parse_args():
    with open('version.txt') as version_file:
        version = version_file.read()
    parser = argparse.ArgumentParser(description='Drone Footage Measure', prog='DFM')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)
    arguments = parser.parse_args()
    return arguments


if __name__ == '__main__':
    args = parse_args()
    app.run(host='0.0.0.0', debug=args.debug)
