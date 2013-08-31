from dbmodels import *
from jobs import *

import datetime
import jinja2
import json
import os
import pytz
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

class AboutPage(Handler):
    def render_about(self):
            self.render('about.html')
    def get(self):
            self.render_about()

class ShowStationHistory(MainPage):
    def render_show_history(
            self, 
            station_req="",
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):

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
        if bikes_req=="" and docks_req=="" and errors_req=="":
            bikes_req = "checked"

        # find the name of the station for the provided ID
        n = StationInfo.all().filter('station_id', int(station_req)).get()
        name = n.name

        # and print it to the logs
        logging.debug(
            '%s, %s, bikes: %s, docks: %s, errors: %s',
            name,
            time_req,
            bikes_req,
            docks_req,
            errors_req
            )

        self.render(
                'history.html',
                bikes_req=bikes_req,
                docks_req=docks_req, 
                errors_req=errors_req,
                station_req=station_req,
                stations=stations,
                time_req=time_req,
                timespans=timespans
                )

    def get(self):
        self.render_show_history()

class HistoryChartHandler(ShowStationHistory):
    def render_history_chart(
            self, 
            station_req="",
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):
        # options for time range dropdown menu, with name and value in 
        # seconds (UNIX time for python)
        timespans = [
                ['past 24 hours', 86400],
                ['past 48 hours', 172800],
                ['past 72 hours', 259000],
                ['past 7 days', 604800],
                ['past 30 days', 2592000]
                ]

        # set defaults
        if station_req == "":
            station_req = 357
        if time_req == "":
            time_req = timespans[0][1]
        if bikes_req=="" and docks_req=="" and errors_req=="":
            bikes_req = "checked"

        min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
        min_time = min_time.replace(microsecond=0)
        
        # filtered for one station, using the provided ID,
        # filtered for a given time range, using min_time
        # provide all the status info sorted from old to new
        history = db.GqlQuery(
            "SELECT * FROM StationStatus \
             WHERE station_id = :1 \
             AND date_time > :2 \
             ORDER BY date_time ASC",
             station_req,
             min_time
             )

        # prep data for insertion into html template
        data_set = []
        if bikes_req=="checked" and docks_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.availableBikes, h.availableDocks, h.errors])
                color = ['#4ECDC4', '#FF6B6B', '#C44D58']
        elif bikes_req=="checked" and docks_req == "checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.availableBikes, h.availableDocks])
                color = ['#4ECDC4', '#FF6B6B']
        elif bikes_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.availableBikes, h.errors])
                color = ['#4ECDC4', '#C44D58']
        elif docks_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.availableDocks, h.errors])
                color = ['#FF6B6B', '#C44D58']
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
        elif errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.errors])
                color = ['#C44D58']

        # find the name of the station for the provided ID
        n = StationInfo.all().filter('station_id', int(station_req)).get()
        name = n.name

        self.render(
                'historychart.js',
                bikes_req=bikes_req,
                data_set=data_set,
                docks_req=docks_req, 
                errors_req=errors_req,
                name=name,
                station_req=station_req,
                time_req=time_req,
                color=color
                )

    def get(self):
        station_req = int(self.request.get('station_req'))
        time_req = int(self.request.get('time_req'))
        bikes_req = self.request.get('bikes_req')
        docks_req = self.request.get('docks_req')
        errors_req = self.request.get('errors_req')
        self.render_history_chart(
            station_req=station_req,
            time_req=time_req,
            bikes_req=bikes_req,
            docks_req=docks_req,
            errors_req=errors_req
            )

class HistoryChartJSONHandler(ShowStationHistory):
    def render_history_chart_json(
            self, 
            station_req="",
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):
        # options for time range dropdown menu, with name and value in 
        # seconds (UNIX time for python)
        timespans = [
                ['past 24 hours', 86400],
                ['past 48 hours', 172800],
                ['past 72 hours', 259000],
                ['past 7 days', 604800],
                ['past 30 days', 2592000]
                ]

        # set defaults
        if station_req == "":
            station_req = 357
        if time_req == "":
            time_req = timespans[0][1]
        if bikes_req=="" and docks_req=="" and errors_req=="":
            bikes_req = "checked"

        min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
        min_time = min_time.replace(microsecond=0)
        
        # filtered for one station, using the provided ID,
        # filtered for a given time range, using min_time
        # provide all the status info sorted from old to new
        history = db.GqlQuery(
            "SELECT * FROM StationStatus \
             WHERE station_id = :1 \
             AND date_time > :2 \
             ORDER BY date_time ASC",
             station_req,
             min_time
             )

        # prep options for insertion
        options = dict(height=500, fontSize=14, fontName='Arial', lineWidth=3, isStacked='true')
        options.update(backgroundColor=dict(stroke="#FFFFFF"))
        options.update(legend=dict(position="top"))
        options.update(chartArea=dict(left=35, top=50, width="80%", height="80%"))
        options.update(hAxis=dict(baselineColor="#FFFFFF", gridlines=dict(color="#FFFFFF")))
        options.update(vAxis=dict(baselineColor="#556270", gridlines=dict(color="#556270", format="#")))
        options.update()
        
        # prep data structure
        cols = []
        rows = []
        time_col = dict(id='Time', type='datetime')
        cols.append(time_col)

        # populate data rows and columns
        if bikes_req=="checked" and docks_req=="checked" and errors_req=="checked":
            cols.append(dict(id='Available bikes', type='number'))
            cols.append(dict(id='Available docks', type='number'))
            cols.append(dict(id='Station errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableBikes))
                row.append(dict(v=h.availableDocks))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#FF6B6B', '#C44D58'])
        
        elif bikes_req=="checked" and docks_req == "checked":
            cols.append(dict(id='Available bikes', type='number'))
            cols.append(dict(id='Available docks', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableBikes))
                row.append(dict(v=h.availableDocks))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#FF6B6B'])
        
        elif bikes_req=="checked" and errors_req=="checked":
            cols.append(dict(id='Available bikes', type='number'))
            cols.append(dict(id='Station errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableBikes))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#C44D58'])
        
        elif docks_req=="checked" and errors_req=="checked":
            cols.append(dict(id='Available docks', type='number'))
            cols.append(dict(id='Station errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableDocks))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FF6B6B', '#C44D58'])
        
        elif bikes_req == "checked":
            cols.append(dict(id='Available bikes', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableBikes))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4'])
        
        elif docks_req == "checked":
            cols.append(dict(id='Available docks', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.availableDocks))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FF6B6B'])
        
        elif errors_req=="checked":
            cols.append(dict(id='Station errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#C44D58'])

        # find the name of the station for the provided ID
        n = StationInfo.all().filter('station_id', int(station_req)).get()
        name = n.name
        options.update(title=name)
        
        # prep json variables
        chartType = 'AreaChart'
        containerID = 'chart_div'
        dataTable = dict(cols=cols, rows=rows)
        # options already prepared

        dict_output = dict(chartType=chartType, containerID=containerID, dataTable=dataTable, options=options)
        json_output = json.dumps(dict_output)
        self.response.out.write(json_output)

    def get(self):
        station_req = int(self.request.get('station_req'))
        time_req = int(self.request.get('time_req'))
        bikes_req = self.request.get('bikes_req')
        docks_req = self.request.get('docks_req')
        errors_req = self.request.get('errors_req')
        self.render_history_chart_json(
            station_req=station_req,
            time_req=time_req,
            bikes_req=bikes_req,
            docks_req=docks_req,
            errors_req=errors_req
            )

class StationErrorChecker(MainPage):
        def render_error_checker(self):
            # pull all updates, sorted most to least recent, and get the first result    
            q = StationStatus.all().order('-date_time').get()
            last = q.date_time
            last_update = last.strftime('%I:%M:%S %p on %A, %B %d, %Y')
            last_update_msg = 'Last update: '+last_update+' UTC.'

            stations = db.GqlQuery(
                "SELECT station_id, errors \
                 FROM StationStatus \
                 WHERE date_time = :1 \
                 ORDER BY station_id ASC",
                 last
                 )

            data_set = []
            for station in stations:
                name_lookup = StationInfo.all().filter('station_id =',station.station_id).get()
                if name_lookup == None:
                    logging.debug("We have a station_id without info: %d", station.station_id)
                    continue
                else:
                    station_name = name_lookup.name
                    ooo_docks = station.errors
                    java_name = '"'+station_name+'"'
                    data_set.append([java_name, ooo_docks])
            sorted_set = sorted(data_set, key=lambda arg: arg[1], reverse=True)
            sorted_set = sorted_set[:10]
            self.render('errors.html', data_set=sorted_set, last_update_msg=last_update_msg)

        def get(self):
		self.render_error_checker()

class TotalBikesAndDocks(MainPage):
    def render_show_totals(
            self,
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):
        # options for time range dropdown menu, with name and value in 
        # seconds (UNIX time for python)
        timespans = [
                ['past 24 hours', 86400],
                ['past 48 hours', 172800],
                ['past 72 hours', 259000],
                ['past 7 days', 604800],
                ['past 30 days', 2592000]
                ]

        # set defaults
        if time_req == "":
            time_req = timespans[1][1]
        if bikes_req=="" and docks_req=="" and errors_req=="":
            bikes_req = "checked"

        min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
        min_time = min_time.replace(microsecond=0)
        
        # filtered for one station, using the provided ID,
        # filtered for a given time range, using min_time
        # provide all the status info sorted from old to new

        history = db.GqlQuery(
            "SELECT * FROM Totals \
             WHERE date_time > :1 \
             ORDER BY date_time ASC",
             min_time
             )

        # prep data for insertion into html template
        data_set = []
        if bikes_req=="checked" and docks_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.bikes, h.docks, h.errors])
                color = ['#4ECDC4', '#FF6B6B', '#C44D58']
        elif bikes_req=="checked" and docks_req == "checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.bikes, h.docks])
                color = ['#4ECDC4', '#FF6B6B']
        elif bikes_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.bikes, h.errors])
                color = ['#4ECDC4', '#C44D58']
        elif docks_req=="checked" and errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.docks, h.errors])
                color = ['#FF6B6B', '#C44D58']
        elif bikes_req == "checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.bikes])
                color = ['#4ECDC4']
        elif docks_req == "checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.docks])
                color = ['#FF6B6B']
        elif errors_req=="checked":
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                data_set.append([tj, h.errors])
                color = ['#C44D58']

        logging.debug(
            'Totals: timespan: %s, bikes: %s, docks: %s, errors: %s',
            time_req,
            bikes_req,
            docks_req,
            errors_req
            )

        self.render(
                'totals.html',
                bikes_req=bikes_req,
                data_set=data_set,
                docks_req=docks_req, 
                errors_req=errors_req,
                time_req=time_req,
                timespans=timespans,
                color=color
                )

    def get(self):
        self.render_show_totals()

    def post(self):
        time_req = int(self.request.get('time_req'))
        bikes_req = self.request.get('bikes_req')
        docks_req = self.request.get('docks_req')
        errors_req = self.request.get('errors_req')
        self.render_show_totals(
            time_req=time_req,
            bikes_req=bikes_req,
            docks_req=docks_req,
            errors_req=errors_req
            )


########## This is where the utils go ##########
def makeJavaScriptTimeForCharts(db_entry):
        t=db_entry.date_time #extract date_time from a data store object
        t_UNIX=t.strftime('%s')+'000' #convert to UNIX time in milliseconds from Python date_time obj
        return int(t_UNIX)
        # return 'new Date(' + t_UNIX + ')' #return JavaScript to add dates and times to charts

########## This is where the task queue handlers go ##########

class FixTimesQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/fixtimes',FixTimesQ) or similar to "app" at the bottom of this script.
    def get(self):
        deferred.defer(FixTimes)
        self.response.out.write('Successfully initiated FixTimes.')

class RemoveTzFixedQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/removetzfixed',RemoveTzFixedQ) or similar to "app" at the bottom 
    # of this script.
    def get(self):
        deferred.defer(RemoveTzFixed)
        self.response.out.write('Successfully initiated RemoveTzFixed.')

class BackfillErrorsDataQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/backfillerrorsdata',BackfillErrorsDataQ) or similar to "app" at the 
    # bottom of this script.
    def get(self):
        deferred.defer(BackfillErrorsData)
        self.response.out.write('Successfully initiated BackfillErrorsData.')

class BackfillTotalsDataQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/backfilltotalsdata',BackfillErrorsDataQ) or similar to "app" at the 
    # bottom of this script.
    def get(self):
        deferred.defer(BackfillTotalsData)
        self.response.out.write('Successfully initiated BackfillTotalsData.')

class ClearBadTimesQ(webapp2.RequestHandler):
    # No longer in use. Removed from webapp2 to prevent it from being 
    # run again by accident. Can re-enable this handler simply by adding
    # ('/clearbadtimes',ClearBadTimesQ) or similar to "app" at the 
    # bottom of this script.
    def get(self):
        deferred.defer(ClearBadTimes)
        self.response.out.write('Successfully initiated ClearBadTimes.')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/about', AboutPage),
                               ('/updatestatus',UpdateStatus),
                               ('/updateall',UpdateAll),
                               ('/errors',StationErrorChecker),
                               ('/totals',TotalBikesAndDocks),
                               ('/history',ShowStationHistory),
                               ('/historychart',HistoryChartHandler),
                               ('/historyjson',HistoryChartJSONHandler)
                               ],
                              debug=True)
