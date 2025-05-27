# Install Drone Video Measure from source code

Here is a short guide on installing the Drone Video Measure programme from source.

```{Note}
If you just want to run the program the easiest solution is to follow this [guide](install.md).
```

## Install dependencies
Prior to installing Drone Video Measure the following dependencies need to be installed.
- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Please verify that Docker Desktop is running properly before continuing. If the Docker window displays "Docker Desktop starting ..." for an extended amount of time, you might need to reboot your computer.

## Install the Drone Video Measure programme
From Powershell (windows) or command line (Mac / Linux):
```bash
git clone https://github.com/egemose/DroneVideoMeasure.git
cd DroneVideoMeasure
./dvm.sh start
```

After running  the `./dvm.sh start` command, a new command line window should open, display some information and then disappear. The first time the command is executed, all the dependencies for the drone video program is downloaded which can take up to ten minutes.

The program is now running as a webserver. To access it do the following:
- Open a Web Browser at [http://localhost:5000](http://localhost:5000).
If Drone Video Measure appears all is set and up and running.

Drone Video Measure runs the following containers:

- Drone Video Measure - Main app
- Drone VIdeo Measure - As background worker
- Redis - for Celery broker
- PostgreSQL - as database storage

## Stopping the programme
To stop a running instance of the programme enter the following command in the terminal.
```bash
./dvm.sh stop
```

## Restarting the programme
After having stopped the programme or having rebooted the computer, the programme needs to be started again. Open a commandline (Powershell in Windows) and enter the following command.
```bash
cd DroneVideoMeasure
./dvm.sh start
```

## Rebuilding the programme

If the source code is changes, the program can be rebuilt using the command
```bash
./dvm.sh build
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
