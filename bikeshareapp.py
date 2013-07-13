from datetime import datetime
from time import sleep
import jinja2, os, traceback
import json, urllib2, time, webapp2
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
	def set_secure_cookie(self, user_id, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (user_id, cookie_val))
	def read_secure_cookie(self, user_id):
		cookie_val = self.request.cookies.get(user_id)
		return cookie_val and check_secure_val(cookie_val)
	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))
	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
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
	def getData(self):
                bikeShareJSON = urllib2.Request('http://www.citibikenyc.com/stations/json')
                response = urllib2.urlopen(bikeShareJSON)
                the_page = response.read()
                return the_page
	def render_front(self, the_page=""):
                the_page = self.getData()
                self.render('front.html', the_page=the_page)
	def get(self):
		self.render_front()

class ShowStationData(MainPage):
        def render_show_data(self, date_time="", status_messages=""):
                q = StationStatus.all().order('-date_time').get()
		last = q.date_time
		last_update = last.strftime('%I:%M:%S %p on %A, %B %d, %Y')
		date_time = 'Last update: '+last_update+'.'
		status_messages = []
                for station in db.GqlQuery("SELECT station_id, name FROM StationInfo ORDER BY station_id ASC"):
                        status = StationStatus.all().filter('station_id =',station.station_id).order('-date_time').get()
                        message = station.name+' has '+str(status.availableBikes)+' available bikes.'
                        status_messages.append(message)
                self.render('show.html', date_time=date_time, status_messages=status_messages)
	def get(self):
		self.render_show_data()

class ShowStationHistory(MainPage):
        def render_show_history(self, history="", date_time="", availableBikes="", availableDocks=""):
                station_req = 357
                availableBikesSeries = []
                availableDocksSeries = []
                x_axis = []
                history = db.GqlQuery("SELECT * FROM StationStatus WHERE station_id = 357 ORDER BY date_time ASC")
                for h in history:
                        availableBikesSeries.append(int(h.availableBikes))
                        print 'added '+str(h.availableBikes)+' to the bikes list.'
                        availableDocksSeries.append(int(h.availableDocks))
                        print 'added '+str(h.availableDocks)+' to the docks list.'
                        x_axis.append(h.date_time)
                        print 'added '+str(h.date_time)+' to the time stamps.'
                print availableBikesSeries
                print availableDocksSeries
                print x_axis
                self.render('history.html', history=history, date_time=date_time, availableBikes=availableBikes, availableDocks=availableDocks)
	def get(self):
		self.render_show_history()


class StationErrorChecker(MainPage):
        def render_error_checker(self):
		q = StationStatus.all().order('-date_time').get()
		last = q.date_time
		last_update = last.strftime('%I:%M:%S %p on %A, %B %d, %Y')
		msg = 'Last update: '+last_update+'.'+'<br><br>'
		self.write(msg)
		for station in db.GqlQuery("SELECT station_id, name FROM StationInfo ORDER BY station_id ASC"):
                        status = StationStatus.all().filter('station_id =',station.station_id).order('-date_time').get()
                        if (status.availableBikes+status.availableDocks) == status.totalDocks:
                                message = station.name+' looks good.<br>'
                        else:
                                message = station.name+' has '+str(status.availableBikes)+' bikes and '+str(status.availableDocks)+' docks, but supposedly '+str(status.totalDocks)+' docks overall.<br>'
                        self.write(message)
	def get(self):
		self.render_error_checker()

class TotalBikesAndDocks(MainPage):
        def render_total_bikes(self):
		q = StationStatus.all().order('-date_time').get()
		last = q.date_time
		last_update = last.strftime('%I:%M:%S %p on %A, %B %d, %Y')
		msg = 'Last update: '+last_update+'.'+'<br><br>'
		self.write(msg)
		total_bikes = 0
		total_docks = 0
		for station in db.GqlQuery("SELECT station_id, name FROM StationInfo ORDER BY station_id ASC"):
                        status = StationStatus.all().filter('station_id =',station.station_id).order('-date_time').get()
                        total_bikes+=status.availableBikes
                        total_docks+=status.availableDocks
                message = 'There are '+str(total_bikes)+' bikes and '+str(total_docks)+' docks available in all of the NYC bike share.<br><br><br><br>hai :D'
                self.write(message)
	def get(self):
		self.render_total_bikes()

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

app = webapp2.WSGIApplication([('/', MainPage),('/show',ShowStationData),('/updatestatus',UpdateStatus),('/updateall',UpdateAll),('/errors',StationErrorChecker),('/totals',TotalBikesAndDocks), ('/history',ShowStationHistory)], 
debug=True)
