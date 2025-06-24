Security
========

Even though **DVM** is build as a web server and can be deployed as such, it is not meant to be hosted on a server and accessed over the internet. **DVM** is made to be run locally without access form external network or as minimum isolated to local network.

The decision to use a web interface comes from a wish of running cross-platform where containers seemed as the best options. Since the goal never was to make a web server for external access the containers and web interface is not made with Security in mind and may have known vulnerabilities.

So running **DVM** with public access is at your own risk and we do not recommend. But if you must do it, at least use a reverse proxy with authentication.
