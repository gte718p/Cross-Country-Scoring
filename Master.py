#!/usr/bin/env python3

import gpxpy
import EvenDist
import csv
import Distance
from datetime import datetime, timedelta
import argparse
import dateutil.parser
import time

error =10  #allowable GPS error in meters
segmentdistance = 100 #distance the race route is divided into in meters
timeerror=600 #should be equal to longest possible time a car could take to traverse between two race points notionaly (segment distance/min speed)



class carpoint:   #defines a data point class of each data point recorded in the log file
    def __init__(self, time, latitude, longitude, state):
        self.time=time
        self.lat = latitude
        self.long=longitude
        self.state=state



class racepoint: # creates a data point class for each race route.
    def __init__(self, latitude, longitude):
        self.time=[]
        self.lat = latitude
        self.long=longitude
        self.state='error'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
#    parser.add_argument('route_file')
    parser.add_argument('day_file')
    parser.add_argument('car_file')
    args = parser.parse_args()






x=[]

starttime=time.time()

#open the car file

carfile=open(args.car_file,'r')
cardata =csv.reader(carfile)

# conver file to readable list store in class
cardata=list(cardata)

i=1

while i < len(cardata):
    eventtime = dateutil.parser.parse(cardata[i][1])
    temp=carpoint(eventtime,cardata[i][2],cardata[i][3],cardata[i][5].strip())
    x.append(temp)
    i+=1
    

#open the days race route
raceroutefile= open(args.day_file,'r')
raceroute=gpxpy.parse(raceroutefile)

# Join all the points from all segments for the track into a single list
racepoints = [p for s in raceroute.tracks[0].segments for p in s.points]

#divide race route into equal length segments
raceroutetemp=EvenDist.interpolate_distance(racepoints, segmentdistance)


#convert GPX to the class
raceroutefinal=[]
i=0

while i < len(raceroutetemp):
    temp=racepoint(raceroutetemp[i].latitude,raceroutetemp[i].longitude,)
    raceroutefinal.append(temp)
    i+=1




points=0
carpoints=0


#compare each point on the race route to each of the available data points

while points < len(raceroutefinal):
    print('Still working: racepoint',points)
    carpoints=0
    while carpoints < len(x):
        dist=100*Distance.haversine(float(x[carpoints].lat),float(x[carpoints].long),float(raceroutefinal[points].lat),float(raceroutefinal[points].long))
        if dist < error:
            if raceroutefinal[points].state != 'DRIVING':
                raceroutefinal[points].time=x[carpoints].time
                raceroutefinal[points].state=x[carpoints].state
           
        carpoints +=1
    points +=1


#create an output file 
i=0    
with open('OutputRaw.txt','w+') as f:
    while i < len(raceroutefinal):
        print(i, raceroutefinal[i].lat, raceroutefinal[i].long,raceroutefinal[i].time, raceroutefinal[i].state, sep=', ',file=f)
        i +=1 
f.close()     

#error checking
errors=[]
errorflag=0
i=0

while i < len(raceroutefinal):
    if str(raceroutefinal[i].state) == 'error':
        if ((i-1) >= 0) & ((i+1) < len(raceroutefinal)):
            if raceroutefinal[i-1].state ==  raceroutefinal[i+1].state:  #one missing data point
                raceroutefinal[i].state = raceroutefinal[i-1].state
                #time calculations

                if ((raceroutefinal[i-1].time != []) & (raceroutefinal[i+1].time != [])):
                    intervaltime=raceroutefinal[i+1].time - raceroutefinal[i-1].time
                    if (intervaltime.seconds < timeerror ):
                        raceroutefinal[i].time = raceroutefinal[i-1].time +((raceroutefinal[i+1].time-raceroutefinal[i-1].time))/2
                    else:
                        raceroutefinal[i].time = raceroutefinal[i-1].time
        if ((i-1) >= 0) & ((i+2) < len(raceroutefinal)):
            if raceroutefinal[i-1].state ==  raceroutefinal[i+2].state: #two missing data points
                raceroutefinal[i].state = raceroutefinal[i-1].state
                if ((raceroutefinal[i-1].time != []) & (raceroutefinal[i+2].time != [])):
                    intervaltime=raceroutefinal[i+2].time - raceroutefinal[i-1].time
                    if (intervaltime.seconds < timeerror ):
                        raceroutefinal[i].time = raceroutefinal[i-1].time +((raceroutefinal[i+2].time-raceroutefinal[i-1].time))/3
                    else:
                        raceroutefinal[i].time = raceroutefinal[i-1].time
    i+=1

#set the error flag for review
i=0
while i < len(raceroutefinal):
    if str(raceroutefinal[i].state) == 'error':
        errorflag=1
        errors.append(i)
    i+=1
                


#create an output file 
i=0    
with open('OutputCorrected.txt','w+') as f:
    while i < len(raceroutefinal):
        print(i, raceroutefinal[i].lat, raceroutefinal[i].long,raceroutefinal[i].time, raceroutefinal[i].state, sep=', ',file=f)
        i +=1 
f.close()     


#count the miles traveled
print('starting distance calc')
DistanceTraveled=0


i=0
cumulativetime=timedelta()
while i < len(raceroutefinal):
    if str(raceroutefinal[i].state) == 'DRIVING':
        DistanceTraveled += segmentdistance
        if ((i > 0) & (raceroutefinal[i-1].time != [])):
            temptime = (raceroutefinal[i].time-raceroutefinal[i-1].time)
            if temptime.seconds < timeerror:
                cumulativetime=cumulativetime+temptime
    i+=1

endtime=time.time()    
print('Total distance traveled: ',DistanceTraveled/1000, ' km')
print('Total time driving: ', cumulativetime)
if errorflag:
    print('There may be error please review the log file at lines', errors)
print('Run time: ', endtime - starttime)


