# Howto - Install Drone Video Measure
Here is a short guide on installing the Drone Video Measure programme.

## Install dependencies
Prior to installing Drone Video Measure the following dependencies need to be installed. 
- [Git](https://git-scm.com/downloads)
- [Docker](https://www.docker.com/)
- [Docker-compose](https://docs.docker.com/compose/install/) (only on Linux)

Please verify that Docker Desktop is running properly before continuing. If the Docker window displays "Docker Desktop starting ..." for an extended amount of time, you might need to reboot your computer. 

## Install the Drone Video Measure programme
From Powershell (windows) or command line (Mac / Linux):
```bash
git clone https://github.com/egemose/DroneVideoMeasure.git
cd DroneVideoMeasure
./dvm.sh start
```

After running  the `./dvm.sh start` command, a new command line window should open, display some information and then dissapear. The first time the command is executed, all the dependencies for the drone video program is downloaded which can take up to ten minutes.

The program is now running as a webserver. To access it do the following:
- Open a Web Browser at [http://localhost:5000](http://localhost:5000).
If Drone Video Measure appears all is set and up and running.

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
