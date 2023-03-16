# Reference - Drone logfile input format
To get information about the location, altitude and orientation of the camera, information from the drone log file is used. The format exported from `AirData.com` is described in this document. 

DVM expects that the uploaded drone log file is a comma separated file, containing the following columns:
- `time(millisecond)`
- `datetime(utc)`
- `latitude`
- `longitude`
- `height_above_takeoff(meters)`
- `altitude_above_seaLevel(meters)`
- `height_sonar(meters)`
- `isVideo`
- `gimbal_heading(degrees)`
- `gimbal_pitch(degrees)`
- `gimbal_roll(degrees)`
- `altitude(meters)`

## Descriptions of the data columns
### `time(millisecond)`
The `time(millisecond)` column contains the number of miliseconds since the UAV was turned on. Usually there is a new line in the logfile every `200 ms`.
Example value: `15600`

### `datetime(utc)`
The `datetime(utc)` column contains a timestamp formatted as `%Y-%m-%d %H:%M:%S`. Usually there is a new line in the logfile every `200 ms`.
Example value: `2023-03-02 10:10:59`.

### `latitude`
The location of the camera specified with the latitude coordinate.
Example value: `555.4497224420358`.

### `longitude`
The location of the camera specified with the longitude coordinate.
Example value: `10.6607664524964.

### `height_sonar(meters)`
The altitude of the camera given in meters as measured by the sonar.
Example value: `15.5`

### `isVideo`
This column indicates whether the camera is recording video or not. It can contain two values, either a zero or a one. The video recorder is active when the value is one..

### `gimbal_heading(degrees)`
The compas direction of the camera, specified in degrees. A value of zero means that the camera is oriented towards north.
Example value: `190.9`

### `gimbal_pitch(degrees)`
The pitch/elevation of the camera in degrees. A value of zero means that the camera is pointing directly towards the horizon. A value of -90 corresponds to a camera that is pointing directly downwards.
Example value: `-90`.

### `gimbal_roll(degrees)`
The roll of the camera. If zero the horizon is level in the recorded video and images.
Example value: `0`.


