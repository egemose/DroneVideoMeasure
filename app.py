import os
import logging.handlers
from flask import Flask, send_from_directory, render_template
from projects.projects import projects_view
from projects.video_gallery import video_gallery_view
from video.videos import videos_view
from drone.drones import drones_view
from home import home_view
from app_config import AppConfig, data_dir, dropzone, obscure, make_celery, db, migrate
from flask_script import Manager
from flask_migrate import MigrateCommand

logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
log_dir = os.path.join(data_dir, 'logs')
log_file = os.path.join(log_dir, 'python.log')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
fh = logging.handlers.TimedRotatingFileHandler(log_file, when='midnight', backupCount=2)
formatter = logging.Formatter('{asctime} | {name:<20} | {levelname:<8} - {message}', style='{')
fh.setFormatter(formatter)
logger.addHandler(fh)


def serve_data_file(filename):
    return send_from_directory(os.path.join('data'), os.path.split(filename)[-1])


def serve_node_modules(filename):
    return send_from_directory(os.path.join('..', '/node_modules'), filename)


def page_not_found(e):
  return render_template('404.html'), 404


def create_app():
    app = Flask(__name__)
    app.register_error_handler(404, page_not_found)
    app.config.from_object(AppConfig)
    app.add_url_rule('/data/<path:filename>', endpoint='data', view_func=serve_data_file)
    app.add_url_rule('/node_modules/<path:filename>', endpoint='node_modules', view_func=serve_node_modules)
    dropzone.init_app(app)
    obscure.init_app(app)
    celery = make_celery(app)
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(projects_view)
    app.register_blueprint(videos_view)
    app.register_blueprint(drones_view)
    app.register_blueprint(home_view)
    app.register_blueprint(video_gallery_view)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    return manager, app, celery


manager, app, celery = create_app()

if __name__ == '__main__':
    manager.run()
