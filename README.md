# M5AtomClock
Python Code to use the M5 Atom Matrix as a small clock

The Atom Matrix has this nice 5x5 LED matrix.

In order to help learn about it.  I decided to try to make a small clock.

The Hours light up around the outside (Not counting the 4 corners, there are 12 LEDs).
The Minutes will be the next ring in (there are 8 LEDs in that ring, so the minutes will only be approximate)
The Seconds will flash the middle LED.

Once a day (round about midnight), I reset the clock from the NTP servers.

This probably isn't the most accurate clock ever created. But then the minutes are only approximate (each LED represents a little less than 8 minutes)

I origionally started to do this with the Blocky code from the UiFlow software that M5 supplies.  And I got most of it working, except for one custom block that I created to do the call to the NTP server.

I just got direct of dragging blocks, and picking from lists, or entering numbers.  So I switched to normal Python.
