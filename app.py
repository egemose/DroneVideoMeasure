import os
import logging.handlers
from flask import Flask, send_from_directory
from projects import projects_view
from video.videos import videos_view
from misc import misc_view
from drone.drones import drones_view
from app_config import AppConfig, data_dir, dropzone, obscure, celery, db, migrate
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


def serve_projects_file(filename):
    return send_from_directory(os.path.join(data_dir, 'projects'), filename)


def create_app():
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    app.config.update(CELERY_BROKER_URL='redis://redis:6379/0', CELERY_RESULT_BACKEND='redis://redis:6379/0')
    app.add_url_rule('/projects/<path:filename>', endpoint='projects_folder', view_func=serve_projects_file)
    dropzone.init_app(app)
    obscure.init_app(app)
    celery.conf.update(app.config)
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(projects_view)
    app.register_blueprint(videos_view)
    app.register_blueprint(misc_view)
    app.register_blueprint(drones_view)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    return manager, app


manager, app = create_app()

if __name__ == '__main__':
    manager.run()
