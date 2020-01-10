import os
import logging.handlers
from flask import Flask, send_from_directory
from flask_dropzone import Dropzone
from flask_obscure import Obscure
import argparse
from projects import projects_view
from video.videos import videos_view
from misc import misc_view
from drone.drones import drones_view
from app_config import AppConfig
from help_functions import base_dir

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
log_dir = os.path.join(base_dir, 'logs')
log_file = os.path.join(log_dir, 'python.log')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
fh = logging.handlers.TimedRotatingFileHandler(log_file, when='midnight', backupCount=2)
formatter = logging.Formatter('{asctime} | {name:<20} | {levelname:<8} - {message}', style='{')
fh.setFormatter(formatter)
logger.addHandler(fh)


def serve_projects_file(filename):
    return send_from_directory(os.path.join(base_dir, 'projects'), filename)


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
    logger.debug(f'App started with args: {args}')
    app.run(host='0.0.0.0', debug=args.debug)
