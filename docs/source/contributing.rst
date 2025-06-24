Contributing
============

Thank you for your interest in contributing to *DVM* and we welcome all pull request. To get set for development on *DVM* see the following.

*DVM* runs as a stack of docker containers:

* dvm_app: main container running the code and build from the docker file.
* dvm_worker: A copy of dvm_app running Celery for offloading long running process such as video file conversion.
* redis: Broker for Celery
* PostgreSQL: Database for storing project data and annotations.

*DVM* is build as a `Flask <https://flask.palletsprojects.com/en/stable/>`_ application as the python backend and uses `Node.js <https://nodejs.org/en>`_ to handle JavaScript dependencies. The python dependencies are listed in *requirements.txt* and Node.js dependencies in *package.json*.

.. note::
    Python version 3.12 or newer is required.


Pre-commit
----------

Development uses pre-commit for code linting and formatting. To setup development with pre-commit follow these steps after cloning the repository:

Create a virtual environment with python:

.. code-block:: shell

    python -m venv venv

Activate virtual environment:

.. code-block:: shell

    source venv/bin/activate

Install *DVM* python package as editable with the development dependencies:

.. code-block:: shell

    pip install -e .[dev]

Install pre-commit hooks

.. code-block:: shell

    pre-commit install

You are now ready to contribute.

Running DVM in development mode
-------------------------------

To run *DVM* in development mode a docker compose file *docker-compose-dev.yml* is used. *docker-compose-dev.yml* adds the code as a bind mount so any changes to code is reflected in the container. The *app_data* folder is also changed to a bind mount at *./data* for easy access to persistent data. The Flask application is run in development mode so errors are shown. An *Adminer* container is also started for access to the database.

To run *DVM* in development mode use:

.. code-block:: shell

    docker compose -f docker-compose.yml -f docker-compose-dev.yml up

And to stop and remove the containers:

.. code-block:: shell

    docker compose -f docker-compose.yml -f docker-compose-dev.yml down

If changes are made to the docker image, a new version can be build with:

.. code-block:: shell

    docker compose -f docker-compose.yml -f docker-compose-dev.yml build

The *dvm.sh* script can also be used to build, start, stop and run in development mode. For example to start in development mode:

.. code-block:: shell

    ./dvm.sh start --dev

Use the following for a list of all commands:

.. code-block:: shell

    ./dvm.sh --help

Running Test
------------

Test is automatically run when making a commit, but can also be run with:

.. code-block:: shell

    pytest

This will also generate a html coverage report in *test_coverage*.

Generating Documentation
------------------------

To generate this documentation, in the *docs* folder run:

.. code-block:: shell

    make html

This will generate html documentation in the *docs/build/html* folder.

Creating Github Release
-----------------------

When a new release is desired from the commits to the master branch, the following steps will create a new release and bump the version number:

* Change version number in :code:`src/dvm/__init__.py` and commit to master.
* Tag the commit with the version number: :code:`git tag vXX.XX.XX`.
* Push the changes to github: :code:`git push origin` (where origin is the name of github upstream).
* push the tag to github: :code:`git push origin tag vXX.XX.XX`.

This will start the github actions to create a new release and publish the code to PyPI together with generating the new documentation.

Changing database version
-------------------------

When changing to a new database version in the *docker-compose.yml* file a new version of the *docker-compose.db_upgrade.yml* must be made and manually added to the github release with the new database version.

The volume names for the old and new version needs updating together with the pinned version of PostgreSQL.
