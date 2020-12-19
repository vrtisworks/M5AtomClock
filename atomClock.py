# A simple little clock for the Atom Matrix
# vrtisworks
# v1.0 - November 2020
# v2.0 - December 2020
# 
# Picked up the time from the RTM each second because counting it drifted too much
# Lowered the intensity of the corners so they were not quite as obvious
# Added a button click to turn the display on and off

from m5stack import *
from m5ui import *
from uiflow import *
import wifiCfg
import time
from numbers import Number
import struct,socket,utime,machine

apName='PrimarySSID'
apPassword='**password**'
altName='AlternateSSID'
altPassword='**password**'

# Time zone offset from GMT
timeZoneOffset=-5*60*60
hourTicks=0       # Once a day around midnight - we want to go get the updated ntp time
# Seconds we just toggle the Dot on and off
currentSecond = False
currentHour = 0
currentMinute = 0
whichDot = 0    # A work variable for when we are calculating dots to light
# The second is always just one dot in the middle
secondDot = 13
# This uses more memory, but runs faster
minuteMap = [
  08,08,08,08,08,08,08,08,
  09,09,09,09,09,09,09,  
  14,14,14,14,14,14,14,14,
  19,19,19,19,19,19,19,
  18,18,18,18,18,18,18,18,
  17,17,17,17,17,17,17,
  12,12,12,12,12,12,12,12,
  07,07,07,07,07,07,07]
# This will be quicker when I need to turn all the minutes off
minuteClear=[08,09,14,19,18,17,12,07]
#          00,01,02,03,04,05,06,07,08,09,10,11
#          12,13,14,15,16,17,18,19,20,21,22,23
hourMap = [ 3, 4,10,15,20,24,23,22,16,11, 6, 2]
# We start with the dots 'on' 
showDots=True
currentTime = ()
maxTicks=0
    
# When we initially turn on the dots (either from a button toggle, or at startup)
# It assumes all the dots are already off
def turnDotsOn():
  global currentHour,currentMinute,currentTime,secondDot,minuteMap,minuteDot,hourMap,whichDot,maxTicks
  currentTime=utime.localtime()
  currentHour = currentTime[3]
  currentMinute = currentTime[4]
  print(currentTime)
  # Put purple in the corners so it doesn't look like the hours
  rgb.setColor(1,0x330033)
  rgb.setColor(5,0x330033)
  rgb.setColor(21,0x330033)
  rgb.setColor(25,0x330033)
  # Then turn on the dots up to the current time (note: range doesn't inlcude the last number)
  # Minutes are 0-59
  for whichDot in range(currentMinute+1):
    rgb.setColor(minuteMap[whichDot],0x00ff00)
  # We only have a 12 hour clock (look out the window to determine am/pm)
  # Hours go 0-23
  if currentHour>11:
    currentHour=currentHour-12
  for whichDot in range(currentHour+1):
    rgb.setColor(hourMap[whichDot],0xff0000)
  print('Minute: ' + str(currentMinute)+' Dot:' + str(minuteMap[currentMinute]))
  print('Hour: ' + str(currentHour)+' Dot:' + str(hourMap[currentHour]))
  print('MaxTicks: '+str(maxTicks))
  # Reset just in case it was >12
  currentHour = currentTime[3]
    
# Toggle the show dots from on to off or off to on
def toggleShow():
  global showDots
  if showDots:
    # If it WAS true, we want to make it false and turn off all the dots.
    showDots=False
    rgb.setColorAll(0x000000)
  else:
    # If it WAS false, we want to make it true and turn on the necessary dots
    showDots=True
    turnDotsOn()

def updateTime():
  global timeZoneOffset
  setNTPtime(timeZoneOffset)

@timerSch.event('handleTimer')
def thandleTimer():
  global currentHour,currentMinute,currentSecond,secondDot,minuteMap,minuteClear,hourMap,whichDot,showDots,currentTime,maxTicks
  ticks=time.ticks_ms()
  # If we aren't showing dots, we have nothing to do
  if not showDots:
    return
  # Otherwise, get the current time (because counting seconds doesn't work)
  currentTime=utime.localtime()
  # print(currentTime)
  # Seconds alternate green/purple
  if currentSecond:
    rgb.setColor(secondDot, 0x0000ff)
    currentSecond=False
  else:
    rgb.setColor(secondDot, 0xff00ff)
    currentSecond=True
  if currentHour != currentTime[3]:
    currentHour=currentTime[3]
    # A new hour... need to turn off all the minutes
    for whichDot in minuteClear:
      rgb.setColor(whichDot,0x000000)
    currentMinute=currentTime[4]
    rgb.setColor(minuteMap[currentMinute], 0x00ff00)
    # If it is noon or midnight - we need to turn all the other hour dots off
    if currentHour==0 or currentHour==12:
      for whichDot in hourMap:
        rgb.setColor(whichDot,0x000000)
    whichDot=currentHour
    if whichDot>11:
      whichDot=whichDot-12
    rgb.setColor(hourMap[whichDot],0xff0000)
    # print('currentHour:'+str(currentHour))
    print (currentTime)
  if currentMinute != currentTime[4]:
    currentMinute=currentTime[4]
    # A new Minute - just need to turn on the dot for that minute
    rgb.setColor(minuteMap[currentMinute], 0x00ff00)
    # print('currentMinute:'+str(currentMinute))
  ticks=time.ticks_ms()-ticks
  if ticks>maxTicks:
    maxTicks=ticks
    print('Ticks in Timer:'+str(ticks))
  pass
  
def setNTPtime(tzoffset,host="pool.ntp.org"):
  # https://github.com/micropython/micropython/blob/master/ports/esp8266/modules/ntptime.py
  # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
  NTP_DELTA = 3155673600
  NTP_QUERY = bytearray(48)
  NTP_QUERY[0] = 0x1B
  addr = socket.getaddrinfo(host, 123)[0][-1]
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
  finally:
    s.close()
  val = struct.unpack("!I", msg[40:44])[0]
  val=val-NTP_DELTA+tzoffset
  print("val:"+str(val))
  tm=utime.localtime(val)
  print(tm)
  # (year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
  machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
  # machine.RTC().datetime((2020,12,17,0,11,59,59,0))
  
def loopTime(loops):
  for i in range(loops):
    wait(1)
    print(utime.localtime())

# ######################################################################################
# Main initialization
# ###################################################################################### 
rgb.setBrightness(10)  
rgb.setColorAll(0x330033)

# First thing is we need to see/connect to wifi
# Need to figure out where - Nick or Matt
wifiCfg.wlan_sta.active(True)
networks = wifiCfg.wlan_sta.scan()
for ssid, bssid, channel, rssi, authmode, hidden in networks:
  ssid = ssid.decode('utf-8')
  if ssid==altName:
    apName=altName
    apPassword=altPassword
  
if not (wifiCfg.wlan_sta.isconnected()):
  print('Connecting to '+apName)
  wifiCfg.doConnect(apName, apPassword)
  while not (wifiCfg.wlan_sta.isconnected()):
    wait(1)
    print('Waiting to connect')
print('Wifi Connected')

# Get the clock from ntp and set the real time clock
updateTime()
# Turn off all the dots
rgb.setColorAll(0x000000)
# This will turn on the Dots necessary to show current time
turnDotsOn()
hourTicks= 23 - currentHour
# Set up the callback for the button press
btnA.wasPressed(toggleShow)
# Then crank up the time for 1 second intervals
timerSch.run('handleTimer', 1000, 0x00)
# Basically... we do nothing until about 'midnight' when we update the clock from NTP
while True:
  if hourTicks<0:
    print('Updating time from NTP')
    # Reset the time from NTP so we don't drift too far
    # Stop the timer because updating it as the NTP time is fetched doesn't work well
    timerSch.stop('handleTimer')
    updateTime()
    # If we are showing the dots.. we need to turn them off
    # Then immediately back on with the 'new' time
    if showDots:
      toggleShow()
      toggleShow()
    # If the dots weren't on.. then we don't have to worry.
    # Now we can start the timer back up.
    timerSch.run('handleTimer', 1000, 0x00)
    # After we get back from that, we can start the wait again
    hourTicks=24
  # Then just sleep for an hour and check it again
  time.sleep(3600)
  # time.sleep(60)
  hourTicks=hourTicks-1
  print('hourTicks:'+str(hourTicks))
  
