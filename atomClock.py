from m5stack import *
from m5ui import *
from uiflow import *
import wifiCfg
import time
from numbers import Number
import struct,socket,utime,machine

apName='**DEFAULTSSID'
apPassword='defaultpassword'
altName='**ALTERNATESSID'
altPassword='alternatepassword'

# Time zone offset from GMT
timeZoneOffset=-5*60*60
hourTicks=0       # Once a day around midnight - we want to go get the updated ntp time
currentSecond = 0
currentHour = 0
currentMinute = 0
minuteDot = 0    # The last minute dot we light up
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
hourMap = [4, 10, 15, 20, 24, 23, 22, 16, 11, 6, 2, 3]

def updateTime():
  global currentSecond, currentHour, currentMinute, timeZoneOffset
  ntpTime = setNTPtime(timeZoneOffset)
  # Get the numbers we want, and make them zero based.
  currentHour = ntpTime[3]-1
  currentMinute = ntpTime[4]-1
  currentSecond = ntpTime[5]-1
  print(ntpTime)

@timerSch.event('handleTimer')
def thandleTimer():
  global currentHour,currentMinute,currentSecond,secondDot,minuteMap,minuteDot,hourMap,hourDot, whichDot,hourTicks
  startTick=time.ticks_ms()
  currentSecond = currentSecond + 1
  # Seconds alternate green/purple
  if currentSecond % 2 == 0:
    rgb.setColor(secondDot, 0x0000ff)
  else:
    rgb.setColor(secondDot, 0xff00ff)
  # print('Second:'+str(currentSecond))
  if currentSecond > 59:   
    currentSecond = 0
    currentMinute = currentMinute+ 1
    print('Minute:' + str(currentMinute)+' Dot:' + str(minuteDot))
  if currentMinute > 59:
    # Need to turn off all the minute dots
    # I assume the code to handle a setColor is a lot longer than a few extra if's
    # So we only set 'black' once for each dot
    minuteDot=-1
    for whichDot in minuteMap:
      if whichDot!=minuteDot:
        minuteDot=whichDot
        rgb.setColor(whichDot,0x000000)
    # And minute is back to 0
    currentMinute = 0
    minuteDot=minuteMap[0]
    rgb.setColor(minuteDot, 0x00ff00)
    # Now handle the hour change
    currentHour = currentHour + 1
    # Check for PM
    if currentHour>11:
      # Need to reset to all black
      for whichDot in hourMap:
        rgb.setColor(whichDot,0x000000)
      currentHour=0
    # Then turn on the current dot
    rgb.setColor(hourMap[currentHour], 0xff0000)
    hourTicks=hourTicks-1
    print('Hour:' + str(currentHour)+' Dot:' + str(hourMap[currentHour]))
  else:
    # We don't need to worry about the hour.. just light a dot if necessary
    whichDot=minuteMap[currentMinute]
    # See if we need to light a new dot
    if whichDot != minuteDot:
      minuteDot = whichDot
      rgb.setColor(minuteDot, 0x00ff00)
  # print('Ticks:'+str(time.ticks_diff(time.ticks_ms(),startTick)))
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
  tm=utime.localtime(val)
  # (year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
  machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
  return tm
  
rgb.setBrightness(10)  
rgb.setColorAll(0xff0000)

# First thing is we need to see/connect to wifi
# Need to figure out where - so we scan for SSID's around us.
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
# Put purple in the corners so it doesn't look like the hours
rgb.setColor(1,0xff00ff)
rgb.setColor(5,0xff00ff)
rgb.setColor(21,0xff00ff)
rgb.setColor(25,0xff00ff)
# Then turn on the dots up to the current time (note: range doesn't inlcude the last number)
for whichDot in range(currentMinute+1):
  rgb.setColor(minuteMap[whichDot],0x00ff00)
if currentHour>11:
  currentHour=currentHour-12
for whichDot in range(currentHour+1):
  rgb.setColor(hourMap[whichDot],0xff0000)
print('Second:'+str(currentSecond));
print('Minute:' + str(currentMinute)+' Dot:' + str(minuteMap[currentMinute]))
print('Hour:' + str(currentHour)+' Dot:' + str(hourMap[currentHour]))
# Then crank up the time for 1 second intervals
timerSch.run('handleTimer', 1000, 0x00)
hourTicks= 23 - currentHour
# Basically... we do nothing until about 'midnight' when we update the clock from NTP
while True:
  if hourTicks<0:
    # Reset the time from NTP so we don't drift too far
    updateTime()
    hourTicks=24
  # Then just sleep for an hour and check it again
  time.sleep(3600)
  
