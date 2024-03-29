# Stereomaton

It is an itinerant self-service stereoscopic (3D) photo automaton.

## Status

Working prototype

It was tested in a festival and it worked wonderfully.

## Related links

Presentation of the project: https://www.crowdsupply.com/virt2real/stereopi/updates/field-report-stereomaton

First photos in the festival: https://photos.haum.org/albums/teriaki2019/

Presentation of the case: https://www.crowdsupply.com/virt2real/stereopi/updates/field-report-follow-up-making-a-case-for-stereomaton

## Overview

Users can use the stereomaton to take photographs of themselves and view them in 3D thanks to appropriate equipment (3D display, cardboard, vr headset, etc.) of their own.
The stereomaton generates a (readable) code they can use to retrieve the photograph on a specific webpage.

## Hardware & base software

The stereomaton is based on [StereoPi](http://stereopi.com/) hardware (board + two cameras)
with SLP variant image of Raspbian (version 0.2.3 used)
with a 3.5" SPI [LCD display](http://www.lcdwiki.com/3.5inch_RPi_Display) using fb_ili9486 driver.

Note that LCD driver and its configuration, touchscreen driver, python as well as evdev, opencv, numpy and pycairo modules are assumed installed on the system for the code present in this repository.
