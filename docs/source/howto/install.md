# Install Drone Video Measure

Here is a short guide on installing the Drone Video Measure programme from source.

```{Note}
If you want to change the source code or similar follow this [guide](install_from_source) instead.
```

## Install dependencies

Prior to installing Drone Video Measure the following dependencies need to be installed.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Please verify that Docker Desktop is running properly before continuing. If the Docker window displays "Docker Desktop starting ..." for an extended amount of time, you might need to reboot your computer.

## Install the Drone Video Measure programme

Download the *docker-compose.yml* from the latest [release](https://github.com/egemose/DroneVideoMeasure/releases/latest).

From Powershell (windows), command line (Mac / Linux) or docker desktop terminal change to the folder where *docker-compose.yml* is saved an run:
```bash
docker compose up
```

The first time the command is executed, all the dependencies for the drone video program is downloaded which can take up to ten minutes.

The program is now running as a webserver. To access it do the following:
- Open a Web Browser at [http://localhost:5000](http://localhost:5000).
If Drone Video Measure appears all is set and up and running.

## Stopping the programme

To stop a running instance of the programme enter the following command in the terminal.
```bash
docker compose down
```

## Uninstalling Drone Video Measure

To uninstall Drone Video Measure remove all docker containers, images and volumes.
```{WARNING}
Running the following commands will permanently delete all Drone Video Measure data.
If using docker for other project then Drone Video Measure the following commands will also remove their container, images and volumes. Instead use docker desktop to only delete Drone Video Measure containers, images and volumes.
```

```bash
docker system prune --all
docker volume prune --all
```
