import datetime
import json
import locale
import os
import time
import traceback

from models import *
from jobs import *
import jinja2
import pytz
import urllib2
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.api import mail
from google.appengine.api.taskqueue import Task

########## All the code in this section is for the regularly scheduled alerts ##########
def sendEmail(
		to=None,
		start_names=None,
		start_bikes=None,
		start_times=None,
		end_names=None,
		end_docks=None,
		end_times=None
):
	body_contents = []

	if len(start_names) > 0:
		body_contents.append('starting stations:\n')

	for key in start_names:
		start_text = '%(start_name)s at %(start_time)s \n\
bikes: %(start_bikes)d \n' % \
		             {'start_time': start_times[key], \
		              'start_bikes': start_bikes[key], \
		              'start_name': start_names[key]}
		body_contents.append(start_text)

	if len(end_names) > 0:
		body_contents.append('\nending stations:\n')

	for key in end_names:
		end_text = '%(end_name)s at %(end_time)s \n\
docks: %(end_docks)d \n' % \
		           {'end_time': end_times[key], \
		            'end_docks': end_docks[key], \
		            'end_name': end_names[key]}
		body_contents.append(end_text)

	body_contents.append('\nenjoy your journey!\n-busybici')

	#cancel_link='http://bikesharepp.appspot.com/delete/'+str(alert_id)+'.'
	#body_contents.append('\n To cancel this alert, click ')
	#body_contents.append(cancel_link)

	body = ''.join(body_contents)
	message = mail.EmailMessage(
		sender='busybici <busybici@bikeshareapp.appspotmail.com>',
		subject='busybici update',
		to=to,
		body=body
	)
	message.send()


def sendSMS(
		to='',
		start_names='',
		start_bikes='',
		start_times='',
		end_names='',
		end_docks='',
		end_times=''
):
	body_contents = []

	if len(start_names) > 0:
		body_contents.append('starting stations:\n')

	for key in start_names:
		start_text = '%(start_name)s at %(start_time)s \n\
bikes: %(start_bikes)d\n' % \
		             {'start_time': start_times[key], \
		              'start_bikes': start_bikes[key], \
		              'start_name': start_names[key]}
		body_contents.append(start_text)

	if len(end_names) > 0:
		body_contents.append('\nending stations:\n')

	for key in end_names:
		end_text = '%(end_name)s at %(end_time)s \n\
docks: %(end_docks)d\n' % \
		           {'end_time': end_times[key], \
		            'end_docks': end_docks[key], \
		            'end_name': end_names[key]}
		body_contents.append(end_text)
	body_contents.append('\n-busybici')

	body = ''.join(body_contents)

	message = mail.EmailMessage(
		sender='busybici <busybici@bikeshareapp.appspotmail.com>',
		subject='',
		to=to,
		body=body
	)
	message.send()


def distribute(
		entity=None,
		start_names=None,
		start_bikes=None,
		start_times=None,
		end_names=None,
		end_docks=None,
		end_times=None
):
	if entity.email != None:
		sendEmail(
			to=entity.email,
			start_names=start_names,
			start_bikes=start_bikes,
			start_times=start_times,
			end_names=end_names,
			end_docks=end_docks,
			end_times=end_times
		)
	if entity.phone != None:
		to = str(entity.phone) + carriers[entity.carrier]
		sendSMS(
			to=to,
			start_names=start_names,
			start_bikes=start_bikes,
			start_times=start_times,
			end_names=end_names,
			end_docks=end_docks,
			end_times=end_times
		)


def generate_msg_info(
		entity
):
	start_names = {}
	start_bikes = {}
	start_times = {}

	end_names = {}
	end_docks = {}
	end_times = {}

	def generate_start_station_info(label='', start_station_id=None):
		start_status = StationStatus.query(StationStatus.station_id == start_station_id).order(
			-StationStatus.date_time).get()
		start_avail_bikes = start_status.availableBikes
		start_time = start_status.date_time
		start_time = convertTime(start_time)
		start_info = StationInfo.query(StationInfo.station_id == start_station_id).get()
		start_name = start_info.name

		start_bikes.update({label: start_avail_bikes})
		start_names.update({label: start_name})
		start_times.update({label: start_time})

	def generate_end_station_info(label='', end_station_id=None):
		end_status = StationStatus.query(StationStatus.station_id == end_station_id).order(
			-StationStatus.date_time).get()
		end_avail_docks = end_status.availableDocks
		end_time = end_status.date_time
		end_time = convertTime(end_time)
		end_info = StationInfo.query(StationInfo.station_id == end_station_id).get()
		end_name = end_info.name

		end_docks.update({label: end_avail_docks})
		end_names.update({label: end_name})
		end_times.update({label: end_time})

	if entity.start1 != None:
		generate_start_station_info(
			label='start1',
			start_station_id=entity.start1
		)
	if entity.start2 != None:
		generate_start_station_info(
			label='start2',
			start_station_id=entity.start2
		)
	if entity.start3 != None:
		generate_start_station_info(
			label='start3',
			start_station_id=entity.start3
		)

	if entity.end1 != None:
		generate_end_station_info(
			label='end1',
			end_station_id=entity.end1
		)
	if entity.end2 != None:
		generate_end_station_info(
			label='end2',
			end_station_id=entity.end2
		)
	if entity.end3 != None:
		generate_end_station_info(
			label='end3',
			end_station_id=entity.end3
		)

	distribute(
		entity=entity,
		start_names=start_names,
		start_bikes=start_bikes,
		start_times=start_times,
		end_names=end_names,
		end_docks=end_docks,
		end_times=end_times
	)


class SendAlerts(webapp2.RequestHandler):
	def send_alerts(self, wait=0):
		todays_alerts = AlertLog.query()

		todays_alerts_len = todays_alerts.filter(AlertLog.complete == False).count()

		if todays_alerts_len == 0:
			logging.debug('Done for the day. See you tomorrow.')
		else:
			while todays_alerts_len > 0:
				current_alerts = todays_alerts.filter(AlertLog.complete == False).order(AlertLog.time)
				a = current_alerts.get()
				now = makeNowTime()
				if a.time <= now:
					generate_msg_info(a)
					logging.debug(
						'I sent an alert that was scheduled for %s.',
						a.time.strftime('%I:%M %p')
					)
					a.complete = True
					a.sent = datetime.datetime.now()
					a.put()
					todays_alerts_len = todays_alerts_len - 1
					time.sleep(1) # give it a second for the new data to take

				else:
					wait = makeWait(a.time)
					logging.debug(
						'Going to count down for %d seconds.',
						wait
					)
					break

			the_only_other_task = Task(payload=None, url="/admin/sendalerts", countdown=wait)
			the_only_other_task.add(queue_name="alertsqueue")

	def post(self):
		self.response.out.write('SendAlerts successfully initiated.')
		self.send_alerts()

class CreateAlerts(webapp2.RequestHandler):
	def create_records(self):
		alert = Alert(
			email='cristina.colon@gmail.com',
			phone=9174552028,
			carrier='AT&T',
			start1=357,
			start2=293,
			start3=483,
			end1=327,
			end2=426,
			end3=147,
			time=datetime.time(20, 0, 0),
			days=[0, 1, 2, 3, 4, 5, 6] # every day of the week
		)
		alert.put()
		alert2 = Alert(
			email='cristina.colon@gmail.com',
			phone=9174552028,
			carrier='AT&T',
			start1=293,
			end1=426,
			time=datetime.time(21, 0, 0),
			days=[0, 6] # weekends
		)
		alert2.put()
		alert3 = Alert(
			email='cristina.colon@gmail.com',
			phone=9174552028,
			carrier='AT&T',
			start1=483,
			end1=147,
			time=datetime.time(21, 15, 0),
			days=[1, 2, 3, 4, 5] # weekdays
		)
		alert3.put()

	def get(self):
		self.create_records()

########## All the code in this section is to send the confirmation emails ##########
def sendConfirmEmail(
		to=None,
		alert_id=None,
		start_names=None,
		start_bikes=None,
		start_times=None,
		end_names=None,
		end_docks=None,
		end_times=None
):
	body_contents = []
	body_contents.append('thanks for signing up! please review your selections and click the below link to confirm them.')
	confirm_url = 'http://bikeshareapp.appspot.com/confirm/'+str(alert_id)
	body_contents.append('\n')
	body_contents.append(confirm_url)

	body = ''.join(body_contents)
	message = mail.EmailMessage(
		sender='busybici <busybici@bikeshareapp.appspotmail.com>',
		subject='confirm your alert selections',
		to=to,
		body=body
	)
	message.send()


########## Utils ##########
def convertTime(t):
	# takes a naive datetime, assigns it the UTC time zone,
	# then converts to NY time
	utc = pytz.timezone('UTC')
	newyork = pytz.timezone('America/New_York')
	t = utc.localize(t)
	t = t.astimezone(newyork)
	t = t.strftime('%I:%M %p')
	return t


def makeNowTime():
	# establish the time zones
	utc = pytz.timezone('UTC')
	newyork = pytz.timezone('America/New_York')

	# make the now, make it aware of its UTC time zone, and convert to NY time
	n = datetime.datetime.now()
	n = utc.localize(n)
	n = n.astimezone(newyork)

	# Reduce to just the time in HH:MM:SS.
	n = n.time()
	n = n.replace(microsecond=0)
	return n


def makeWait(x):
	now = makeNowTime()
	now_seconds = (now.hour * 3600) + (now.minute * 60) + now.second
	next_time = (x.hour * 3600) + (x.minute * 60) + x.second
	diff = next_time - now_seconds

	# Give a few seconds of cushion. This helps make sure that tasks scheduled
	# on the hour and the half hour get the most up-to-date status info.
	diff += 5

	# Disallow negative wait times.
	if diff <= 0:
		return 0
	else:
		# 1 hour max wait time
		wait = min(diff, 3600)
		return wait


carriers = {'AT&T': '@txt.att.net',
            'Qwest': '@qwestmp.com',
            'T-Mobile': '@tmomail.net',
            'Verizon': '@vtext.com',
            'Sprint': '@pm.sprint.com',
            'Virgin Mobile': '@vmobl.com',
            'Nextel': '@messaging.nextel.com',
            'Alltel': '@message.alltel.com',
            'Metro PCS': '@mymetropcs.com',
            'Powertel': '@ptel.com',
            'Boost Mobile': '@myboostmobile.com',
            'Suncom': '@tms.suncom.com',
            'Tracfone': '@mmst5.tracfone.com',
            'U.S. Cellular': '@email.uscc.net'}