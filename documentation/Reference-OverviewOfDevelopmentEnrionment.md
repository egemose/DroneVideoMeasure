# Reference - Overview of development environment

The Drone Video Measure program environment is placed in a docker container. 

The docker container is constructed based on the description in the file `Dockerfile`.

The installed python packages are specified in the `requirements.txt` file.

The installed java script packages are listed in the `package.json` file.

To build the docker container run the command `./dvm.sh build`.

To enter a running docker container, the following can be used
```
$ docker ps
CONTAINER ID   IMAGE                COMMAND                  CREATED         STATUS         PORTS                                       NAMES
162279d49321   dvm                  "/app/entrypoint.sh …"   8 minutes ago   Up 8 minutes   0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   dvm_app
$ docker exec -it 162279d49321 bash
root@162279d49321:/app#
```

