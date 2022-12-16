The Drone Video Measure program is updated from time to time. The process of upgrading an existing installation of the programme is described in this document.

This howto assumes that you have a working installation of Drone Video Measure as described in [Howto - Install Drone Video Measure](Howto-InstallDroneVideoMeasure).

The installation process consists of stopping the programme, updating the files to the new version and then building the programme. After this the programme can be started again. To do this, use the following commands.

To stop Drone Video Measure:
```bash
./dvm.sh stop
```

To update Drone Video Measure:
```bash
./dvm.sh update
```

To build Drone Video Measure if changes is made to the code:
```bash
./dvm.sh build
```


