# Drone Video Measure

A tool to measure and track things on a planar surface.
Developed to measure and track marine mammals in the surface of the ocean.

* [Getting Started](#getting-started)
  - [Using a Docker-hub image](#using-a-docker-hub-image-the-easy-way)
  - [Manual install](#manual-install)
  - [Usage](#usage)
  - [Author](#author)
  - [License](#license)

## Getting Started

### Manual install

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

* To stop Drone Video Measure, type:
```bash
./dvm.sh stop
```

* To rebuild Drone Video Measure, type:
```bash
./dvm.sh rebuild
```

* To update Drone Video Measure, type:
```bash
./dvm.sh update
```

* To uninstall Drone Video Measure, type:
```bash
./dvm.sh remove
```
And delete the DroneVideoMeasure directory.

* On Windows data is stored in a Docker volume and will persist even when DVM is closed. To remove the data, type:
```bash
docker volume rm appmedia
```

* On Mac / Linux data is stored in the data directory and can be removed simply by deleting it.

## Usage

A detailed description of how to use the program can be found here: [Manual](manual/manual.md)

Demo data is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3604005.svg)](https://doi.org/10.5281/zenodo.3604005) including a video demo of how to use the program.

## Supported Drones

* DJI

Currently only flight logs from DJI drones are suppored. If you what support for other drones please create a issue with a flight log attached.

## Author

Written by Henrik Dyrberg Egemose (hesc@mmmi.sdu.dk) as part of the InvaDrone and Back2Nature projects, research projects by the University of Southern Denmark UAS Center (SDU UAS Center).

## License

This project is licensed under the MIT license - see the [LICENSE](LICENSE) file for details.
