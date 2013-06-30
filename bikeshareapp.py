from datetime import datetime
import json, urllib2, time, webapp2
from google.appengine.ext import db

'''
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
		self.uid = self.read_secure_cookie('user_id')
		self.user = self.uid and User.by_id(int(self.uid))
'''

class MainPage(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	def getData(self):
                bikeShareJSON = urllib2.Request('http://www.citibikenyc.com/stations/json')
                response = urllib2.urlopen(bikeShareJSON)
                the_page = response.read()
                return the_page
	def render_front(self):
		self.write("hello world <br><br>")
		self.write(self.getData())
	def get(self):
		self.render_front()

class ShowStationData(MainPage):
        def render_show_data(self):
		self.write("hello here is the data you have stored!<br><br>")
		stations = db.GqlQuery("SELECT * FROM StationInfo ORDER BY station_id DESC")
		for station in stations:
                        status = StationStatus.all().filter('station_id =',station.station_id).order('-date_time').get()
                        #status = status_list.get()
                        avail = status.availableBikes
                        message = station.name+' has '+str(avail)+' available bikes'+'<br><br>'
                        self.write(message)
	def get(self):
		self.render_show_data()

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

class UpdateAll(webapp2.RequestHandler):
	def getData(self):
                bikeShareJSON = urllib2.Request('http://www.citibikenyc.com/stations/json')
                response = urllib2.urlopen(bikeShareJSON)
                the_page = response.read()
                return the_page
	def update_all_data(self):
                raw_data = self.getData()
                data = json.loads(raw_data)
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
			
                        #update StationStatus
                        availableDocks = station_list[i]['availableDocks']
                        totalDocks = station_list[i]['totalDocks']
                        statusKey = station_list[i]['statusKey']
                        availableBikes = station_list[i]['availableBikes']
                        made_key = str(station_id)+'_'+str(et_UNIX)
			r = StationStatus(key_name = made_key, date_time = et, station_id = station_id, availableDocks = availableDocks, totalDocks = totalDocks, statusKey = statusKey, availableBikes = availableBikes, )
			r_key = r.put()
			
			#update StatusInfo
			statusValue = station_list[i]['statusValue']
			r = StatusInfo(key_name = statusValue, statusKey = statusKey, statusValue = statusValue)
                        r_key = r.put()
	def get(self):
		self.update_all_data()

class UpdateStatus(UpdateAll):
	def update_station_status(self):
                raw_data = self.getData()
                data = json.loads(raw_data)
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

app = webapp2.WSGIApplication([('/', MainPage),('/show',ShowStationData),('/updatestatus',UpdateStatus),('/updateall',UpdateAll)], 
debug=True)
