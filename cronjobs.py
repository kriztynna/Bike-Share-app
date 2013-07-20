from dbmodels import *
import datetime
import json
import traceback
import time
import urllib2
import webapp2
from google.appengine.ext import db

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
			r = StationStatus(key_name = made_key, date_time = et, station_id = station_id, availableDocks = availableDocks, totalDocks = totalDocks, statusKey = statusKey, availableBikes = availableBikes)
			r_key = r.put()
	def get(self):
		self.update_station_status()
