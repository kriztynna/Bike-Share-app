from models import *
from jobs import *

import datetime
import jinja2
import json
import locale
import os
import pytz
import time
import traceback
import urllib2
import webapp2

from google.appengine.ext import ndb
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
        stations = ndb.gql("SELECT station_id, name \
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
        n = StationInfo.query(StationInfo.station_id == int(station_req)).get()
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

class HistoryChartJSONHandler(ShowStationHistory):
    def render_history_chart_json(
            self, 
            station_req="",
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):

        min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
        min_time = min_time.replace(microsecond=0)
        
        # filtered for one station, using the provided ID,
        # filtered for a given time range, using min_time
        # provide all the status info sorted from old to new
        history = ndb.gql(
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

        else:
            cols.append(dict(id='',type='number'))
            for h in history:
                tj=makeJavaScriptTimeForCharts(h)
                row=[]
                row.append(dict(v=tj))
                row.append(dict(v=0))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FFFFFF'])

        # find the name of the station for the provided ID
        n = StationInfo.query(StationInfo.station_id == int(station_req)).get()
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
            time_req = timespans[0][1]
        if bikes_req=="" and docks_req=="" and errors_req=="":
            bikes_req = "checked"

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
                docks_req=docks_req, 
                errors_req=errors_req,
                time_req=time_req,
                timespans=timespans
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

class TotalChartJSONHandler(ShowStationHistory):
    def render_totals_chart_json(
            self, 
            time_req="",
            bikes_req="",
            docks_req="",
            errors_req=""
            ):

        min_time = datetime.datetime.now() - datetime.timedelta(seconds=time_req)
        min_time = min_time.replace(microsecond=0)
        
        history = ndb.gql(
            "SELECT * FROM Totals \
             WHERE date_time > :1 \
             ORDER BY date_time ASC",
             min_time
             )

        # prep options for insertion
        options = dict(height=500, fontSize=14, fontName='Arial', lineWidth=3, isStacked='true')
        options.update(backgroundColor=dict(stroke="#FFFFFF"))
        options.update(legend=dict(position="top"))
        options.update(chartArea=dict(left=50, top=50, width="80%", height="80%"))
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
            cols.append(dict(id='Total bikes', type='number'))
            cols.append(dict(id='Total docks', type='number'))
            cols.append(dict(id='Total errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.bikes))
                row.append(dict(v=h.docks))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#FF6B6B', '#C44D58'])
        
        elif bikes_req=="checked" and docks_req == "checked":
            cols.append(dict(id='Total bikes', type='number'))
            cols.append(dict(id='Total docks', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.bikes))
                row.append(dict(v=h.docks))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#FF6B6B'])
        
        elif bikes_req=="checked" and errors_req=="checked":
            cols.append(dict(id='Total bikes', type='number'))
            cols.append(dict(id='Total errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.bikes))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4', '#C44D58'])
        
        elif docks_req=="checked" and errors_req=="checked":
            cols.append(dict(id='Total docks', type='number'))
            cols.append(dict(id='Total errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.docks))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FF6B6B', '#C44D58'])
        
        elif bikes_req == "checked":
            cols.append(dict(id='Total bikes', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.bikes))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#4ECDC4'])
        
        elif docks_req == "checked":
            cols.append(dict(id='Total docks', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.docks))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FF6B6B'])
        
        elif errors_req=="checked":
            cols.append(dict(id='Total errors', type='number'))
            for h in history:
                tj = makeJavaScriptTimeForCharts(h)
                row = []
                row.append(dict(v=tj))
                row.append(dict(v=h.errors))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#C44D58'])

        else:
            cols.append(dict(id='',type='number'))
            for h in history:
                tj=makeJavaScriptTimeForCharts(h)
                row=[]
                row.append(dict(v=tj))
                row.append(dict(v=0))
                c = dict(c=row)
                rows.append(c)
                options.update(colors=['#FFFFFF'])
        
        # prep json variables
        chartType = 'AreaChart'
        containerID = 'chart_div'
        dataTable = dict(cols=cols, rows=rows)
        # options already prepared

        dict_output = dict(chartType=chartType, containerID=containerID, dataTable=dataTable, options=options)
        json_output = json.dumps(dict_output)
        self.response.out.write(json_output)

    def get(self):
        time_req = int(self.request.get('time_req'))
        bikes_req = self.request.get('bikes_req')
        docks_req = self.request.get('docks_req')
        errors_req = self.request.get('errors_req')
        self.render_totals_chart_json(
            time_req=time_req,
            bikes_req=bikes_req,
            docks_req=docks_req,
            errors_req=errors_req
            )

class SuperlativesPage(Handler):
    def render_superlatives(self):
        query = SystemStats.query()
        most_trips = query.order(-SystemStats.trips).get()
        most_trips_date = most_trips.date.strftime('%A, %B %d, %Y')
        most_trips_amt = '{:,}'.format(most_trips.trips)

        least_trips = query.order(SystemStats.trips).get()
        least_trips_date = least_trips.date.strftime('%A, %B %d, %Y')
        least_trips_amt = '{:,}'.format(least_trips.trips)

        most_miles = query.order(-SystemStats.miles).get()
        most_miles_date = most_miles.date.strftime('%A, %B %d, %Y')
        most_miles_amt = '{:,}'.format(most_miles.miles)

        least_miles = query.order(SystemStats.miles).get()
        least_miles_date = least_miles.date.strftime('%A, %B %d, %Y')
        least_miles_amt = '{:,}'.format(least_miles.miles)

        longest_trips = query.order(-SystemStats.miles_per_trip).get()
        longest_trips_date = longest_trips.date.strftime('%A, %B %d, %Y')
        longest_trips_amt = '{:,}'.format(longest_trips.miles_per_trip)

        shortest_trips = query.order(SystemStats.miles_per_trip).get()
        shortest_trips_date = shortest_trips.date.strftime('%A, %B %d, %Y')
        shortest_trips_amt = '{:,}'.format(shortest_trips.miles_per_trip)

        most_day_passes = query.order(-SystemStats.day_passes).get()
        most_day_passes_date = most_day_passes.date.strftime('%A, %B %d, %Y')
        most_day_passes_amt = '{:,}'.format(most_day_passes.day_passes)

        min_time = datetime.datetime.strptime('2013-06-01','%Y-%m-%d')
        least_day_passes = query.filter(SystemStats.date>=min_time).order(SystemStats.date, SystemStats.day_passes).get()
        least_day_passes_date = least_day_passes.date.strftime('%A, %B %d, %Y')
        least_day_passes_amt = '{:,}'.format(least_day_passes.day_passes)

        most_week_passes = query.order(-SystemStats.week_passes).get()
        most_week_passes_date = most_week_passes.date.strftime('%A, %B %d, %Y')
        most_week_passes_amt = '{:,}'.format(most_week_passes.week_passes)

        min_time = datetime.datetime.strptime('2013-06-02','%Y-%m-%d')
        least_week_passes = query.filter(SystemStats.date>=min_time).order(SystemStats.date, SystemStats.week_passes).get()
        least_week_passes_date = least_week_passes.date.strftime('%A, %B %d, %Y')
        least_week_passes_amt = '{:,}'.format(least_week_passes.week_passes)

        most_member_signups = query.order(-SystemStats.signups).get()
        most_member_signups_date = most_member_signups.date.strftime('%A, %B %d, %Y')
        most_member_signups_amt = '{:,}'.format(most_member_signups.signups)

        least_member_signups = query.order(SystemStats.signups).get()
        least_member_signups_date = least_member_signups.date.strftime('%A, %B %d, %Y')
        least_member_signups_amt = '{:,}'.format(least_member_signups.signups)

        latest_entry = query.order(-SystemStats.date).get()
        last_update = latest_entry.date.strftime('%A, %B %d, %Y')
        members = '{:,}'.format(latest_entry.members)
        cum_trips = '{:,}'.format(latest_entry.cum_trips)
        cum_miles = '{:,}'.format(latest_entry.cum_miles)


        self.render(
            'superlatives.html',
            most_trips_date=most_trips_date,
            most_trips_amt=most_trips_amt,
            least_trips_date=least_trips_date,
            least_trips_amt=least_trips_amt,
            longest_trips_date=longest_trips_date,
            longest_trips_amt=longest_trips_amt,
            shortest_trips_date=shortest_trips_date,
            shortest_trips_amt=shortest_trips_amt,
            most_miles_date=most_miles_date,
            most_miles_amt=most_miles_amt,
            least_miles_date=least_miles_date,
            least_miles_amt=least_miles_amt,
            most_day_passes_date=most_day_passes_date,
            most_day_passes_amt=most_day_passes_amt,
            least_day_passes_date=least_day_passes_date,
            least_day_passes_amt=least_day_passes_amt,
            most_week_passes_date=most_week_passes_date,
            most_week_passes_amt=most_week_passes_amt,
            least_week_passes_date=least_week_passes_date,
            least_week_passes_amt=least_week_passes_amt,
            most_member_signups_date=most_member_signups_date,
            most_member_signups_amt=most_member_signups_amt,
            least_member_signups_date=least_member_signups_date,
            least_member_signups_amt=least_member_signups_amt,
            last_update=last_update,
            members=members,
            cum_trips=cum_trips,
            cum_miles=cum_miles
            )

    def get(self):
            self.render_superlatives()

########## This is where the utils go ##########
def makeJavaScriptTimeForCharts(entity):
        t=entity.date_time #extract date_time from a data store object
        t_UNIX=t.strftime('%s')+'000' #convert to UNIX time in milliseconds from Python date_time obj
        return int(t_UNIX)

########## Task Queue ##########
class MakeMilesPerTripQ(webapp2.RequestHandler):
    def get(self):
        deferred.defer(MakeMilesPerTrip)
        self.response.out.write('Make miles per trip successfully initiated.')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/about', AboutPage),
                               ('/updatestatus',UpdateStatus),
                               ('/updateall',UpdateAll),
                               ('/totals',TotalBikesAndDocks),
                               ('/totalsjson',TotalChartJSONHandler),
                               ('/history',ShowStationHistory),
                               ('/historyjson',HistoryChartJSONHandler),
                               ('/updatesystemstats',UpdateSystemStats),
                               ('/superlatives',SuperlativesPage),
                               ('/makemilespertrip',MakeMilesPerTripQ)
                               ],
                              debug=True)
