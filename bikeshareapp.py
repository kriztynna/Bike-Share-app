from dbmodels import *
from jobs import *

import datetime
import jinja2
import json
import os
import time
import traceback
import urllib2
import webapp2

from google.appengine.ext import db
from google.appengine.ext import deferred

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
	# more things I will probably need later, but don't right now:
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
        def render_show_history(
                self, station_req="",
                time_req="",
                bikes_req="",
                docks_req=""):
                # options for time range dropdown menu, with name and value in 
                # seconds (UNIX time for python)
                timespans = [
                        ['past 24 hours', 86400],
                        ['past 48 hours', 172800],
                        ['past 72 hours', 259000],
                        ['past 7 days', 604800],
                        ['past 30 days', 2592000]
                        ]

                # Options for the dropdown menu of bike stations. Pulls up 
                # every known station_id, and the name. Note: The projection 
                # seems to only work with at least two fields projected.
                stations = db.GqlQuery("SELECT station_id, name \
                        FROM StationInfo \
                        ORDER BY station_id ASC")

                # set defaults
                if station_req == "":
                        station_req = 357
                if time_req == "":
                        time_req = timespans[0][1]
                if bikes_req=="" and docks_req == "":
                        bikes_req = "checked"

                min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
                min_time = min_time.replace(microsecond=0)
                
                # filtered for one station, using the provided ID,
                # filtered for a given time range, using min_time
                # provide all the status info sorted from old to new
                q_id = "station_id = "+str(station_req)
                q_time = "date_time > DATETIME('"+str(min_time)+"')"
                q = "SELECT * \
                        FROM StationStatus \
                        WHERE " + q_id + " AND " + q_time + \
                        " ORDER BY date_time ASC"
                history = db.GqlQuery(q)

                # prep data for insertion into html template
                data_set = []
                if bikes_req=="checked" and docks_req == "checked":
                        for h in history:
                                tj = makeJavaScriptTimeForCharts(h)
                                data_set.append([tj, h.availableBikes, h.availableDocks])
                                color = ['#4ECDC4', '#FF6B6B']
                elif bikes_req == "checked":
                        for h in history:
                                tj = makeJavaScriptTimeForCharts(h)
                                data_set.append([tj, h.availableBikes])
                                color = ['#4ECDC4']
                elif docks_req == "checked":
                        for h in history:
                                tj = makeJavaScriptTimeForCharts(h)
                                data_set.append([tj, h.availableDocks])
                                color = ['#FF6B6B']

                # find the name of the station for the provided ID
                n = StationInfo.all().filter('station_id', int(station_req)).get()
                name = n.name
                msg = name+", "+str(time_req)+", bikes: "+bikes_req+", docks: "+docks_req
                print msg # will print to the app engine logs for later reference
                self.render(
                        'history.html',
                        bikes_req=bikes_req,
                        data_set=data_set,
                        docks_req=docks_req, 
                        name=name,
                        station_req=station_req,
                        stations=stations,
                        time_req=time_req,
                        timespans=timespans,
                        color=color
                        )

	def get(self):
		self.render_show_history()

	def post(self):
                station_req = int(self.request.get('station_req'))
                time_req = int(self.request.get('time_req'))
                bikes_req = self.request.get('bikes_req')
                docks_req = self.request.get('docks_req')
                self.render_show_history(
                        station_req=station_req,
                        time_req=time_req,
                        bikes_req=bikes_req,
                        docks_req=docks_req
                        )


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
                sorted_set = sorted_set[:10]
                self.render('errors.html', data_set=sorted_set, last_update_msg=last_update_msg)

        def get(self):
		self.render_error_checker()

class TotalBikesAndDocks(MainPage):
        def render_total_bikes(self):
                totals = []

		# using station 72 as a filter because have not been able to
                # implement a better method to ensure unique date_time values
		history = db.GqlQuery("SELECT * FROM StationStatus \
                        WHERE station_id = 72 \
                        ORDER BY date_time ASC \
                        LIMIT 8")
		
		for h in history:
                        java_time = makeJavaScriptTimeForCharts(h)
                        def give_totals():
                                total_bikes = 0
                                total_docks = 0
                                s_query = db.GqlQuery("SELECT station_id, name \
                                        FROM StationInfo \
                                        ORDER BY station_id ASC")
                                for station in s_query:
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

########## This is where the task queue handlers go ##########

class FixTimesQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/fixtimes',FixTimesQ) or similar to "app" at the bottom of this script.
    def get(self):
        deferred.defer(FixTimes)
        self.response.out.write('Successfully initiated.')

class RemoveTzFixedQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/removetzfixed',RemoveTzFixedQ) or similar to "app" at the bottom 
    # of this script.
    def get(self):
        deferred.defer(RemoveTzFixed)
        self.response.out.write('Successfully initiated.')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/updatestatus',UpdateStatus),
                               ('/updateall',UpdateAll),
                               ('/errors',StationErrorChecker),
                               ('/totals',TotalBikesAndDocks),
                               ('/history',ShowStationHistory)
                               ],
                              debug=True)
