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

.. _manual_test:

Manual Test
-------------------

To run a manual test we will use the test dataset from `zenodo <https://doi.org/10.5281/zenodo.3604005>`_. Then follow these steps to test must aspects of the program:

#. Make sure DVM is started from a clean build.
    * Delete all DVM containers (:code:`docker container prune`)
    * Delete all volumes (:code:`docker volume prune --all`)
    * Run DVM in dev mode (:code:`./dvm.sh start --dev`)
#. Open DVM at `http://localhost:5000 <http://localhost:5000>`_.
#. Create a new Drone.
    * Give the drone a name and a description of camera settings.
    * Upload calibration video.
    * When calibration is done check calibration by clicking on view calibration.
#. Create a new Project
    * Give the Project a name and a description.
    * Choose the created drone.
    * upload Drone log file.
#. Upload Video to Project.
    * Open the project and upload the *DJI_0013.MOV* file.
    * When conversion is complete check that video thumbnail is shown.
#. Test video concatenating **Optional**.
    * Upload another *DJI_0013.MOV* file.
    * Concatenate the 2 videos and give the output video a name.
#. Open a Video and make an Annotation.
    * Open a video and choose a frame to make a annotation.
    * Make a point annotation and verify it shows in *Doodles*.
    * make a line annotation and verify it shows in *Doodles*.
    * Add a new annotation group and give it a name.
    * Make a point annotation and verify it shows in the new annotation group.
    * make a line annotation and verify it shows in the new annotation group.
#. Test Misc.
    * Make sure the video plays and controls work.
    * Add artificial horizon and world corners and check if it matches the video.
    * Show plot of drone log and verify video position.
    * Download annotations from video.
    * Download annotations from project.
    * Download logs.
#. Test Clean Up.
    * Remove Project.
    * Remove Drone.
    * verify files have been removed.

Creating Github Release
-----------------------

When a new release is desired from the commits to the master branch, the following steps will create a new release and bump the version number:

* Change version number in :code:`src/dvm/__init__.py` and commit to master.
* Tag the commit with the version number: :code:`git tag vXX.XX.XX`.
* Push the changes to github: :code:`git push origin` (where origin is the name of github upstream).
* push the tag to github: :code:`git push origin tag vXX.XX.XX`.

This will start the github actions to create a new release and publish the container to ghcr.io. The workflow needs to be approved by either Henrik Dyrberg Egemose or Henrik Skov Midtiby.

.. note::
    Before the publishing can be approved a manual test of the program have to be run. See :ref:`manual_test`.

Changing database version
-------------------------

When changing to a new database version in the *docker-compose.yml* file a new version of the *docker-compose.db_upgrade.yml* must be made and manually added to the github release with the new database version.

The volume names for the old and new version needs updating together with the pinned version of PostgreSQL.
