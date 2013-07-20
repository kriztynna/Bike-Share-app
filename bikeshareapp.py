import datetime
from time import sleep
import jinja2
import json
import os
import time
import traceback
import urllib2
import webapp2
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

########## This is where the web page handlers go ##########

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
	# don't need this yet: self.uid = self.read_secure_cookie('user_id')
	# don't need this yet either: self.user = self.uid and User.by_id(int(self.uid))
	#more things I will probably need later, but don't right now:
	'''
        def set_secure_cookie(self, user_id, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (user_id, cookie_val))
	def read_secure_cookie(self, user_id):
		cookie_val = self.request.cookies.get(user_id)
		return cookie_val and check_secure_val(cookie_val)
	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))
	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')'''

class MainPage(Handler):
	def render_front(self):
                self.render('front.html')
	def get(self):
		self.render_front()

class ShowStationHistory(MainPage):
        def render_show_history(self, station_req="", time_req=""):
                # options for drop down, name and value in seconds
                # (UNIX time for python)
                timespans = [
                        ['past 24 hours', 86400],
                        ['past 48 hours', 172800],
                        ['past 72 hours', 259000],
                        ['past 7 days', 604800],
                        ['past 30 days', 2592000]
                        ]
                if time_req == "":
                        time_req = timespans[4][1]
                min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
                min_time = min_time.replace(microsecond=0)
                
		# Pull up every known station_id, and the name, bc the projection only seems
                # to work with at least two fields
                stations = db.GqlQuery("SELECT station_id, name \
                        FROM StationInfo \
                        ORDER BY station_id ASC")

                if station_req == "":
                        station_req = 357

                # filtered for one station, using the provided ID,
                # filtered for a given time range, using min_time
                # provide all the status info sorted from old to new
                q_id = "station_id = "+str(station_req)
                q_time = "date_time > DATETIME('"+str(min_time)+"')"
                q = "SELECT * FROM StationStatus WHERE " + q_id + " AND " + q_time +" ORDER BY date_time ASC"
                history = db.GqlQuery(q)

                # prep data for insertion into html template
                data_set = []
                for h in history:
                        tj = makeJavaScriptTimeForCharts(h)
                        data_set.append([tj, h.availableBikes])

                # find the name of the station for the provided ID
                n = StationInfo.all().filter('station_id', int(station_req)).get()
                name = n.name
                print name # will print to the app engine logs for later reference
                self.render('history.html', data_set=data_set, stations=stations, timespans=timespans, time_req=time_req, name=name, station_req=station_req)

	def get(self):
		self.render_show_history()

	def post(self):
                station_req = int(self.request.get('station_req'))
                time_req = int(self.request.get('time_req'))
                self.render_show_history(station_req=station_req, time_req=time_req)


class StationErrorChecker(MainPage):
        def render_error_checker(self):
		# pull all updates, sorted most to least recent, and get the first result
                q = StationStatus.all().order('-date_time').get()
		last = q.date_time
		last_update = last.strftime('%I:%M:%S %p on %A, %B %d, %Y')
		last_update_msg = 'Last update: '+last_update+'.'
		
		# pull up every known station_id, and the name, bc the projection only works
		# with two or more fields
		stations = db.GqlQuery("SELECT station_id, name \
                                        FROM StationInfo ORDER BY station_id ASC")
		data_set = []
		for station in stations:
                        # filtered for one station, using the provided ID,
                        # provide all the status information sorted from most
                        # to least recent, returning the first result
                        status = StationStatus.all().filter('station_id =',station.station_id).order('-date_time').get()
                        ooo_docks = int(status.totalDocks - (status.availableBikes+status.availableDocks))
                        java_name = '"'+station.name+'"'
                        data_set.append([java_name, ooo_docks])
                sorted_set = sorted(data_set, key=lambda arg: arg[1], reverse=True)
                sorted_set = sorted_set[:9]
                self.render('errors.html', data_set=sorted_set, last_update_msg=last_update_msg)

        def get(self):
		self.render_error_checker()

class TotalBikesAndDocks(MainPage):
        def render_total_bikes(self):
		history = db.GqlQuery("SELECT * FROM StationStatus WHERE station_id = 72 ORDER BY date_time ASC LIMIT 8")
		totals = []
		for h in history:
                        java_time = makeJavaScriptTimeForCharts(h)
                        def give_totals():
                                total_bikes = 0
                                total_docks = 0
                                for station in db.GqlQuery("SELECT station_id, name FROM StationInfo ORDER BY station_id ASC"):
                                        status = StationStatus.all().filter('station_id',station.station_id).filter('date_time', h.date_time).get()
                                        if status == None:
                                                continue
                                        else:
                                                total_bikes+=status.availableBikes
                                                total_docks+=status.availableDocks
                                return total_bikes, total_docks
        		total_bikes, total_docks = give_totals()
                        totals.append([java_time, total_bikes, total_docks])
                self.render('totals.html', totals=totals)                                
	def get(self):
		self.render_total_bikes()


########## This is where the utils go ##########
def makeJavaScriptTimeForCharts(db_entry):
        t=db_entry.date_time #extract date_time from a data store object
        t_UNIX=t.strftime('%s')+'000' #convert to UNIX time in milliseconds from Python date_time obj
        return 'new Date(' + t_UNIX + ')' #return JavaScript to add dates and times to charts

########## This is where the database models go ##########
class StationInfo(db.Model):
        station_id = db.IntegerProperty(required = True)
        name = db.StringProperty(required = True)
        coordinates = db.GeoPtProperty(required = True)
        stAddress1 = db.StringProperty(required = True)
        stAddress2 = db.StringProperty(required = False)

class StationStatus(db.Model):
        station_id = db.IntegerProperty(required = True)
        availableDocks = db.IntegerProperty(required = True)
        totalDocks = db.IntegerProperty(required = True)
        statusKey = db.IntegerProperty(required = True)
        availableBikes = db.IntegerProperty(required = True)
        date_time = db.DateTimeProperty(required = True)

        @classmethod
	def by_id(cls, sid):
                status = StationStatus.all().filter('station_id =', sid).get()
		return status


class StatusInfo(db.Model):
        statusValue = db.StringProperty(required = True)
        statusKey = db.IntegerProperty(required = True)

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
                et = datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
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
                et = datetime.strptime(execution_time, '%Y-%m-%d %I:%M:%S %p')
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

app = webapp2.WSGIApplication([('/', MainPage),('/updatestatus',UpdateStatus),('/updateall',UpdateAll),('/errors',StationErrorChecker),('/totals',TotalBikesAndDocks), ('/history',ShowStationHistory)], 
debug=True)
