from models import *
import csv
import datetime
import json
import logging
import StringIO
import traceback
import time
import urllib2
import webapp2

import pytz
from google.appengine.ext import ndb
from google.appengine.ext import deferred


########## This is where the cron jobs go ##########

class UpdateAll(webapp2.RequestHandler):
    	def getData(self, i=1):
                try:
                        bikeShareJSON = urllib2.Request('http://www.citibikenyc.com/stations/json')
                        response = urllib2.urlopen(bikeShareJSON)
                        raw_data = response.read()
                        data = json.loads(raw_data)
                        return data
                except ValueError:
                        print traceback.format_exc()
                        time.sleep(60*i)
                        self.getData(i+0.25)

        def get_et(self, data):
                execution_time = data['executionTime']
                et = datetime.datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
                newyork = pytz.timezone('America/New_York')
                et = newyork.localize(et)
                et_UNIX = int(time.mktime(et.timetuple()))
                et_UTC = et.astimezone(pytz.UTC)
                et_UTC = et_UTC.replace(tzinfo=None)
                return et, et_UNIX, et_UTC

        def update_all_data(self):
                data = self.getData()
                station_list = data['stationBeanList']

                #update StationInfo
                def enterStation(i):
                        station_id = station_list[i]['id']
                        name = station_list[i]['stationName']
                        lat, lon = float(station_list[i]['latitude']), float(station_list[i]['longitude'])
                        coordinates = ndb.GeoPt(lat, lon)
                        stAddress1 = station_list[i]['stAddress1']
                        stAddress2 = station_list[i]['stAddress2']
                        r = StationInfo(
                            id=str(station_id), 
                            station_id = station_id, 
                            name = name, 
                            coordinates = coordinates, 
                            stAddress1 = stAddress1, 
                            stAddress2 = stAddress2
                            )
                        r_key = r.put()

                for i in range(len(station_list)):
                        #check if entry exists
                        station_id = station_list[i]['id']
                        exists = StationInfo.query(StationInfo.station_id == station_id).get()
                        if exists == None:
                                logging.debug('Inserting new station %d', station_id)
                                enterStation(i)
                        else:
                                enterStation(i)
                        
                        #update StatusInfo
                        statusKey = station_list[i]['statusKey']
                        if statusKey == 1:
                                continue
                        elif statusKey == 3:
                                continue
                        else:
                                statusValue = station_list[i]['statusValue']
                                print 'Found a new status: statusKey = '+str(statusKey)+' and statusValue = '+statusValue+'.'
                                print 'I added this new status to the database BUT *you need to manually update* this code to prevent unnecessary rewrites.'
                        
                        r = StatusInfo(
                            id=statusValue, 
                            statusKey = statusKey, 
                            statusValue = statusValue
                            )

                        r_key = r.put()

        def get(self):
                self.update_all_data()

class UpdateStatus(UpdateAll):
    def update_station_status(self):
        data = self.getData()
        et, et_UNIX, et_UTC = self.get_et(data)
        station_list = data['stationBeanList']
        all_bikes = 0
        all_docks = 0
        all_errors = 0
        to_put_status = []
        for i in range(len(station_list)):
            #update StationStatus
            station_id = station_list[i]['id']
            availableDocks = station_list[i]['availableDocks']
            totalDocks = station_list[i]['totalDocks']
            statusKey = station_list[i]['statusKey']
            availableBikes = station_list[i]['availableBikes']
            made_key = str(station_id)+'_'+str(et_UNIX)
            errors = totalDocks - (availableBikes + availableDocks)

            r = StationStatus(
                id=made_key, 
                date_time = et_UTC, 
                station_id = station_id, 
                availableDocks = availableDocks, 
                totalDocks = totalDocks, 
                statusKey = statusKey, 
                availableBikes = availableBikes, 
                errors = errors
                )

            to_put_status.append(r)
            all_bikes += availableBikes
            all_docks += availableDocks
            all_errors += errors

        t = Totals(
            id=str(et_UNIX), 
            date_time = et_UTC, 
            bikes = all_bikes, 
            docks = all_docks, 
            errors = all_errors
            )

        t.put()
        ndb.put_multi(to_put_status)

    def get(self):
        self.update_station_status()

class UpdateSystemStats(webapp2.RequestHandler):
    def getStats(self):
        systemstats = urllib2.Request('http://cf.datawrapper.de/CSXes/data')
        # possible alternative: 
        # systemstats = urllib2.Request('http://s3.datawrapper.de/CSXes/data')
        response = urllib2.urlopen(systemstats).read()
        raw_data = StringIO.StringIO(response)
        csv_data = csv.reader(raw_data)
        csv_data.next()

        to_put = []
        for row in csv_data:
            date = datetime.datetime.strptime(row[0], '%m/%d/%Y')
            min_date = datetime.datetime.strptime('2013-05-27', '%Y-%m-%d')
            if date < min_date:
                continue
            else:
                made_key = datetime.datetime.strftime(date, '%Y/%m/%d')
                exists = SystemStats.query(SystemStats.date == date).get()
                if exists == None:
                    trips = int(row[1])
                    cum_trips = int(row[2])

                    if row[3] == '':
                        miles = 0
                    else:
                        miles = int(row[3])

                    cum_miles = int(row[4])

                    try:
                        members = int(row[5])
                    except:
                        members = 0

                    signups = int(row[6])
                    day_passes = int(row[7])
                    week_passes = int(row[8])
                    miles_per_trip = miles/trips
                
                    stat = SystemStats(
                        id=made_key,
                        date = date,
                        trips = trips,
                        miles = miles,
                        miles_per_trip = miles_per_trip,
                        cum_trips = cum_trips,
                        cum_miles = cum_miles,
                        members = members,
                        signups = signups,
                        day_passes = day_passes,
                        week_passes = week_passes
                        )

                    to_put.append(stat)
                    logging.debug('New data added.')
                    
                else:
                    continue
        
        ndb.put_multi(to_put)

    def get(self):
        self.getStats()







