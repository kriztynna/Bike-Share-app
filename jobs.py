from dbmodels import *
import datetime
import json
import logging
import traceback
import time
import urllib2
import webapp2

import pytz
from google.appengine.ext import db
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
	def update_all_data(self):
                data = self.getData()
                execution_time = data['executionTime']
                et = datetime.datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
                et = et.replace(tzinfo=pytz.timezone("America/New_York"))
                et_UNIX = int(time.mktime(et.timetuple()))
                station_list = data['stationBeanList']
                for i in range(len(station_list)):
                        #update StationInfo
                        
                        station_id = station_list[i]['id']
                        name = station_list[i]['stationName']
                        coordinates = str(station_list[i]['latitude'])+', '+str(station_list[i]['longitude'])
                        stAddress1 = station_list[i]['stAddress1']
                        stAddress2 = station_list[i]['stAddress2']
			r = StationInfo(key_name = str(station_id), station_id = station_id, name = name, coordinates = coordinates, stAddress1 = stAddress1, stAddress2 = stAddress2)
			r_key = r.put()
			
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
                                r = StatusInfo(key_name = statusValue, statusKey = statusKey, statusValue = statusValue)
                                r_key = r.put()
	def get(self):
		self.update_all_data()

class UpdateStatus(UpdateAll):
	def update_station_status(self):
                data = self.getData()
                execution_time = data['executionTime']
                et = datetime.datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
                et = et.replace(tzinfo=pytz.timezone("America/New_York"))
                et_UNIX = int(time.mktime(et.timetuple()))
                station_list = data['stationBeanList']
                for i in range(len(station_list)):
                        #update StationStatus
			station_id = station_list[i]['id']
			availableDocks = station_list[i]['availableDocks']
                        totalDocks = station_list[i]['totalDocks']
                        statusKey = station_list[i]['statusKey']
                        availableBikes = station_list[i]['availableBikes']
                        made_key = str(station_id)+'_'+str(et_UNIX)
			r = StationStatus(
                                key_name = made_key,
                                date_time = et,
                                station_id = station_id,
                                availableDocks = availableDocks,
                                totalDocks = totalDocks,
                                statusKey = statusKey,
                                availableBikes = availableBikes)
			r_key = r.put()
	def get(self):
		self.update_station_status()

########## This is where the task queue things go ##########
def FixTimes(cursor=None):
        # 5 hours time offset
        offset = datetime.timedelta(seconds=18000)
        limit = 1000
        if cursor == None:
                cursor = 0
        counter = 0
        counter_updated = 0


        prep = "SELECT * FROM StationStatus WHERE date_time < DATETIME('2013-07-22 00:58:01') ORDER BY date_time ASC LIMIT "+str(cursor)+", "+str(limit)
        print prep

        the_times = db.GqlQuery(prep)
        for e in the_times:
                if e.tzFixed != True:
                        old_time = e.date_time
                        new_time = old_time + offset
                        new_time_UNIX = new_time.strftime('%s')
                        e.date_time = new_time
                        e.tzFixed = True
                        e_key = e.put()
                        counter+=1
                        counter_updated+=1
                else:
                        counter+=1
                        continue
        cursor += counter
        if counter > 0:
                logging.debug('Cycled through %d entities and updated %d of them. Cumulative total entities reviewed: %d', counter, counter_updated, cursor)
                deferred.defer(FixTimes, cursor=cursor)
        else:
                logging.debug("I think I'm done??? I updated %d entities in total!", cursor)

def RemoveTzFixed(cursor=0,cum_updated=0,cum_missing=0):
        limit = 500
        counter = 0
        counter_updated = 0
        counter_missing = 0


        prep = "SELECT * FROM StationStatus WHERE date_time < DATETIME('2013-07-22 00:58:01') ORDER BY date_time ASC LIMIT "+str(cursor)+", "+str(limit)
        logging.debug(prep)

        the_list = db.GqlQuery(prep)
        for e in the_list:
                if e.tzFixed == True:
                        ''' The function deletes the named attribute, 
                        provided the object allows it. For example, 
                        delattr(x, 'foobar') is equivalent 
                        to del x.foobar.'''
                        del e.tzFixed
                        e_key = e.put()
                        counter+=1
                        counter_updated+=1
                else:
                        counter+=1
                        counter_missing+=1

        cursor += counter
        cum_updated += counter_updated
        cum_missing += counter_missing

        if counter > 0:
                logging.debug('Cycled through %d entities and updated %d of them. Cumulative totals: reviewed: %d, updated: %d, missing: %d.', counter, counter_updated, cursor, cum_updated, cum_missing)
                deferred.defer(RemoveTzFixed, cursor=cursor, cum_updated=cum_updated, cum_missing=cum_missing)
        else:
                logging.debug("All done. Totals: reviewed: %d, updated: %d, missing: %d.", cursor, cum_updated, cum_missing)



