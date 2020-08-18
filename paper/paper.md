---
title: "DroneVideoMeasure: Using drones to quantify the length of marine animals"
authors:
- affiliation: 1
  name: Henrik Dyrberg Egemose
  orcid: 0000-0002-6765-8216
- affiliation: 1
  name: Henrik Skov Midtiby
  orcid: 0000-0002-3310-5680
date: '2020-01-22'
output: pdf_document
bibliography: paper.bib
tags:
- GUI
- Python
- UAV
- Drones
- Marine animals
affiliations:
- index: 1
  name: UAS Center, University of Southern Denmark
---

# Summary

It is a daunting task to quantify the length of marine mammals like porpoises and seals, as it most often is required to catch the animal before it can be quantified. Using video acquired with an Unmanned Aerial Vehicle (UAV) and then utilizing information about camera position, gimbal tilt and orientation from the flight log of the UAV, it is possible to estimate lengths of marine animals while they are in the water surface and get gps coordinates of the location of the animal. The ``Drone Video Measure`` program enables the user to combine videos recorded by UAVs with information from the flight log. Enabling the user to track the position through the hole video, and choose which frames to measure lengths independent of camera gimbal position. The accuracy of the method was investigated by [@Midtiby2019Havforsker].

With the software marine biologist can estimate the size of marine animals in UAV recordings, using an noninvasive method and with a significantly lower time usage compared to the capture and measure process. Several software systems have been developed to measure marine animals in images taken from UAVs, but all work under the assumption that the UAVs camera is pointing straight down e.g. [@Torres2020; @Burnett2018; @Dawson2017]. This constrain limits the UAV operator and it may be hard to get images if the marine animal is at the surface for a short time period.

The Drone Video Measure software is available at [@Egemose2020VideoDroneMeasure] and is released under the MIT License. The software was developed as part of the Back2Nature project at the University of Southern Denmark.

# Acknowledgements

We want to thank Magnus Wahlberg, Emilie Nicoline Stepien, Sara Torres Ortiz and Gema Palacino-Gonzalez which all have tested early versions of the ``Drone Video Measure`` program and given us valuable insights into the marine environment.

The ``Drone Video Measure`` is currently used in several studies related to harbor porpoises and grey seals at both the  University of Southern Denmark and Aarhus University.

# References
