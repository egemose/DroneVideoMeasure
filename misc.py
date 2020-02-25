import os
import flask
import logging
from zipfile import ZipFile
from app_config import data_dir

logger = logging.getLogger('app.' + __name__)

misc_view = flask.Blueprint('misc', __name__)


@misc_view.route('/version')
def version():
    with open('version.txt') as version_file:
            ver = version_file.read()
    logger.debug(f'Render version')
    return flask.render_template('misc/version.html', version=ver)


@misc_view.route('/download_logs')
def download_logs():
    logger.debug(f'Downloading logs')
    log_dir = os.path.join(data_dir, 'logs')
    file_paths = get_all_file_paths(log_dir)
    log_zip = os.path.join(data_dir, 'logs.zip')
    with ZipFile(log_zip, 'w') as zip_file:
        for file in file_paths:
            zip_file.write(file)
    return flask.send_file(log_zip, as_attachment=True, attachment_filename='logs.zip')


def get_all_file_paths(directory):
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths
