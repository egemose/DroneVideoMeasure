import argparse
from app_config import app
from projects import projects_view

app.register_blueprint(projects_view)


def parse_args():
    with open('version.txt') as version_file:
            version = version_file.read()
    parser = argparse.ArgumentParser(description='Image Annotater Flask App.', prog='Image Annotater')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    app.run(host='0.0.0.0', debug=args.debug)
