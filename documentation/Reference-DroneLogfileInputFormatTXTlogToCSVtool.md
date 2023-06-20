# Reference - Drone logfile input format
To get information about the location, altitude and orientation of the camera, information from the drone log file is used. The format exported from `TXTlogToCSVtool.exe` is described in this document. 

DVM expects that the uploaded drone log file is a comma separated file, containing the following columns:
- `CUSTOM.updateTime`
- `GIMBAL.yaw`
- `GIMBAL.pitch`
- `GIMBAL.roll`
- `OSD.height [m]`
- `CUSTOM.isVideo`
- `OSD.latitude`
- `OSD.longitude`

## Descriptions of the data columns
### `CUSTOM.updateTime`
The `CUSTOM.updateTime` column contains a timestamp formatted as `%Y/%m/%d %H:%M:%S.%f`. Usually there is a new line in the logfile every `100 ms`.
Example value: `2018/07/04 09:19:32.113`.

### `GIMBAL.yaw`
The compas direction of the camera, specified in degrees. A value of zero means that the camera is oriented towards north.
Example value: `151.6`

### `GIMBAL.pitch`
The pitch/elevation of the camera in degrees. A value of zero means that the camera is pointing directly towards the horizon. A value of -90 corresponds to a camera that is pointing directly downwards.
Example value: `-86.3`.

### `GIMBAL.roll`
The roll of the camera. If zero the horizon is level in the recorded video and images.
Example value: `0`.

### `OSD.height [m]`
The altitude of the camera given in meters.
Example value: `10.4`

### `CUSTOM.isVideo`
This column indicates whether the camera is recording video or not. It can contain two values, either the empty string or the string `Recording`.

### `OSD.latitude`
The location of the camera specified with the latitude coordinate.
Example value: `55.507158`.

### `OSD.longitude`
The location of the camera specified with the longitude coordinate.
Example value: `10.717505`.
