To uninstall Drone Video Measure issue the command:
```bash
./dvm.sh remove
```

And delete the DroneVideoMeasure directory.

On Windows data is stored in a Docker volume and will persist even when DVM is closed. To remove the data, issue the command
```bash
docker volume rm appmedia
```

On Mac / Linux data is stored in the data directory and can be removed simply by deleting it.
