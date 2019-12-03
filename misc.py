import flask
import logging

logger = logging.getLogger('app.' + __name__)

misc_view = flask.Blueprint('misc', __name__)


@misc_view.route('/version')
def version():
    with open('version.txt') as version_file:
            ver = version_file.read()
    logger.debug(f'Render version')
    return flask.render_template('misc/version.html', version=ver)
