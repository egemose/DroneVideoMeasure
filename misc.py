import flask

misc_view = flask.Blueprint('misc', __name__)


@misc_view.route('/version')
def version():
    with open('version.txt') as version_file:
            ver = version_file.read()
    return flask.render_template('misc/version.html', version=ver)
