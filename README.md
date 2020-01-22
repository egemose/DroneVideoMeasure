# Drone Video Measure

A tool to measure and track things on a planar surface.
Developed to measure and track marine mammals in the surface of the ocean.

## Getting Started

* Install the following applications:
  - [Git](https://git-scm.com/downloads)
  - [Docker](https://www.docker.com/)
  - [Docker-compose](https://docs.docker.com/compose/install/) (only on Linux)

* From Powershell (windows) or command line (Mac / Linux), type:
```bash
git clone https://github.com/egemose/DroneVideoMeasure.git
cd DroneVideoMeasure
./dvm.sh start
```

* Open a Web Browser at `http://localhost:5000`
  - If Drone Video Measure appears all is set and up and running.

* To stop Drone Video Measure press CTRL+C and run:
```bash
./dvm.sh stop
```

* To rebuild Drone Video Measure run:
```bash
./dvm.sh rebuild
```

## Usage

* First and drone need to be registered and calibrated under the "Drone" menu.
  - A video of a checkerboard (like this [checkerboard.png](checkerboard.png)) is captured with the drone from different angles.
  - Uploading the video and the drones camera is automatically calibrated.
* Then a project can be created.
  - The drone used is selected.
  - One project correspond to one flight i.e one drone log file.
  - A DJI drone log converted to csv is needed.
  Can be done here: [PhantomHelp](https://www.phantomhelp.com/LogViewer/Upload/)
  and Downloading the verbose csv.
  - Videos from that flight are uploaded.
  - Videos can be viewed and annotated

Demo data is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3604005.svg)](https://doi.org/10.5281/zenodo.3604005) including a video demo of how to use the program.

## Author

Written by Henrik Dyrberg Egemose (hesc@mmmi.sdu.dk) as part of the InvaDrone and Back2Nature projects, research projects by the University of Southern Denmark UAS Center (SDU UAS Center).

## License

This project is licensed under the 3-Clause BSD License - see the [LICENSE](LICENSE) file for details.
