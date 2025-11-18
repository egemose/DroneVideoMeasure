# Use a fixed camera

If using a fixed stationary camera the following information is needed:

- Height of camera over the surface of interest.
- GPS coordinates of the camera in latitude and longitude.
- Camera rotation as yaw, pitch and roll.

The cameras GPS coordinates can be obtained from GPS measurements or from google maps by zooming in on the cameras location and right clicking. Yaw, pitch and roll can be measured where yaw is the rotation relative to magnetic north in degrees. 0&deg; is north, 90&deg; is east, 180&deg; is south and 270&deg; is west. Pitch is the cameras angle relative to the horizon, where 0&deg; is looking at the horizon and -90&deg; is looking straight down. Roll is the tilt compared to horizontal,  with 0&deg; meaning horizontal and 90&deg; meaning vertical.

If only relative measurements are desired, such as length in individual frames, GPS coordinates and yaw can be arbitrary. If the camera is pointing straight down (pitch -90&deg;) the roll can also be arbitrary.

In DVM when creating a project, a fixed camera can be used by checking off the "Use Fixed camera instead of drone log" and filling in the needed information. This will create a "fake" logfile for DVM to use with the videos in the project.

Since there is no real logfile with timestamps any annotation will have the same timestamp, but the frame number is given in the output annotations which can be used to calculate relative time between to annotations if needed.
