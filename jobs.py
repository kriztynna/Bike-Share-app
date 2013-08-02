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
        def get_et(self, data):
                execution_time = data['executionTime']
                et = datetime.datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
                newyork = pytz.timezone('America/New_York')
                et = newyork.localize(et)
                et_UNIX = int(time.mktime(et.timetuple()))
                return et, et_UNIX
	def update_all_data(self):
                data = self.getData()
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
                et, et_UNIX = self.get_et(data)
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
                                key_name = made_key,
                                date_time = et, 
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
                        date_time = et,
                        key_name = str(et_UNIX),
                        bikes = all_bikes,
                        docks = all_docks,
                        errors = all_errors
                        )

                db.put(t)
                db.put(to_put_status)

	def get(self):
		self.update_station_status()

########## This is where the task queue things go ##########
def FixTimes(cursor=None, cum_updated=0):
        # 5 hours time offset
        offset = datetime.timedelta(seconds=3600)
        limit = 10000
        if cursor == None:
                cursor = 0
        counter = 0
        counter_updated = 0


        prep = "SELECT * FROM StationStatus WHERE date_time <= DATETIME('2013-07-30 02:59:01') ORDER BY date_time ASC LIMIT "+str(cursor)+", "+str(limit)
        logging.debug(prep)

        the_times = db.GqlQuery(prep)
        for e in the_times:
                if e.tzFixed != True:
                        old_time = e.date_time
                        new_time = old_time - offset
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
        cum_updated += counter_updated
        if counter > 0:
                logging.debug(
                        'Cycled through %d entities and updated %d of them. \
                        Cumulative total entities reviewed: %d, updated: %d', 
                        counter, 
                        counter_updated, 
                        cursor,
                        cum_updated
                        )
                deferred.defer(FixTimes, cursor=cursor, cum_updated=cum_updated)
        else:
                logging.debug(
                        "All done. Reviewed %d entities \
                        and updated %d of them in total!", 
                        cursor, 
                        cum_updated
                        )

def RemoveTzFixed(cursor=0, cum_deleted=0, cum_skipped=0):
        limit = 5000
        counter = 0
        deleted = 0
        skipped = 0
        to_put = []

        prep = "SELECT * FROM StationStatus \
                WHERE date_time <= DATETIME('2013-07-30 11:59:01') \
                ORDER BY date_time \
                ASC LIMIT "+str(cursor)+", "+str(limit)

        logging.debug(prep)

        the_list = db.GqlQuery(prep)
        
        for e in the_list:
                if hasattr(e,'tzFixed'):
                        delattr(e,'tzFixed')
                        to_put.append(e)
                        counter+=1
                        deleted+=1
                else:
                        counter+=1
                        skipped+=1
                        continue

        cursor += counter
        cum_deleted+=deleted
        cum_skipped+=skipped

        if counter > 0:
                db.put(to_put)
                logging.debug(
                        'Cycled through %d entities this round. Deleted %d, skipped %d. \
                        Totals: reviewed: %d, deleted: %d, skipped: %d.', 
                        counter, 
                        deleted,
                        skipped,
                        cursor,
                        cum_deleted,
                        cum_skipped
                        )
                deferred.defer(
                        RemoveTzFixed, 
                        cursor=cursor, 
                        cum_deleted=cum_deleted, 
                        cum_skipped=cum_skipped
                        )
        else:
                logging.debug(
                        "All done. Totals: reviewed: %d, deleted: %d, skipped: %d.", 
                        cursor,
                        cum_deleted,
                        cum_skipped
                        )

def BackfillErrorsData(cursor=0):
        # Through experience making the previous two task queue functions, 
        # I think the optimal batch size is between 500 and 1000
        # 500 is too small, but with 1000, sometimes the operation times out.
        # even with a batch size of 750, sometimes it times out.
        limit = 750
        counter = 0

        prep = "SELECT * FROM StationStatus \
                        WHERE date_time < DATETIME('2013-07-28 22:59:01') \
                        ORDER BY date_time \
                        ASC LIMIT "+str(cursor)+", "+str(limit)
        
        logging.debug(prep)

        the_list = db.GqlQuery(prep)
        for e in the_list:
                errors = e.totalDocks - (e.availableBikes + e.availableDocks)
                e.errors = errors
                e_key = e.put()
                counter+=1

        cursor += counter

        if counter > 0:
                logging.debug(
                        'Filled in errors attribute for %d entities. Cumulative total: %d', 
                        counter, 
                        cursor
                        )
                deferred.defer(BackfillErrorsData, cursor=cursor)
        else:
                logging.debug("All done. Filled in errors attribute for %d entities in total.", cursor)



