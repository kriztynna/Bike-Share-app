import re
import time

from models import *
from alerts import *

import jinja2
import pytz
import urllib2
import webapp2
from google.appengine.ext import ndb

### Handler stuff copied over from main file ###
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

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


### Real code starts here ###
class AlertsForm(Handler):
	def render_alerts_form(
		self, 
		email="",
		alert_type="",
		phone="",
		carrier="",
		start1="",
		start2="",
		start3="",
		end1="",
		end2="",
		end3="",
		time="",
		hour="",
		minute="",
		AMPM="",
		days="",
		email_error="",
		phone_error="",
		carrier_error="",
		start1_error="",
		start2_error="",
		start3_error="",
		end1_error="",
		end2_error="",
		end3_error="",
		days_error="",
		time_error="",
		email_sel="",
		text_sel="",
		both_sel=""
		):
		stations = ndb.gql("SELECT station_id, name \
                FROM StationInfo \
                ORDER BY name ASC")
		stations_dict = dict()
		for s in stations:
			stations_dict[s.station_id] = s.name
		self.render(
			'alerts.html', 
			email=email, 
			alert_type=alert_type,
			phone=phone,
			carrier=carrier,
			start1=start1,
			start2=start2,
			start3=start3,
			end1=end1,
			end2=end2,
			end3=end3,
			hour=hour,
			minute=minute,
			AMPM=AMPM,
			days=days,
			email_error=email_error,
			phone_error=phone_error,
			carrier_error=carrier_error,
			start1_error=start1_error,
			start2_error=start2_error,
			start3_error=start3_error,
			end1_error=end1_error,
			end2_error=end2_error,
			end3_error=end3_error,
			days_error=days_error,
			time_error=time_error,
			email_sel=email_sel,
			text_sel=text_sel,
			both_sel=both_sel,
			stations_dict=stations_dict
			)
	def get(self):
		self.render_alerts_form()
	def post(self):
		self.email = self.request.get('email')
		self.alert_type = self.request.get('alert_type')
		def alertSelected(alert_type):
			self.email_sel, self.text_sel, self.both_sel = '', '', ''
			if alert_type=='email':
				self.email_sel='selected'
			elif alert_type=='textmsg':
				self.text_sel='selected'
			elif alert_type=='both':
				self.both_sel='selected'
		alertSelected(self.alert_type)

		self.phone = self.request.get('phone')
		self.carrier = self.request.get('carrier')

		self.start1 = self.request.get('start1')
		self.start2 = self.request.get('start2')
		self.start3 = self.request.get('start3')

		self.end1 = self.request.get('end1')
		self.end2 = self.request.get('end2')
		self.end3 = self.request.get('end3')

		self.su = self.request.get('su')
		self.mo = self.request.get('mo')
		self.tu = self.request.get('tu')
		self.we = self.request.get('we')
		self.th = self.request.get('th')
		self.fr = self.request.get('fr')
		self.sa = self.request.get('sa')
		def generate_days():
			candidates=[self.su, self.mo, self.tu, self.we, self.th, self.fr, self.sa]
			finalists=[]
			for c in candidates:
				if c!='':
					c = int(c)
					finalists.append(c)
			return finalists
		days = generate_days()

		self.hour = self.request.get('hour')
		self.minute = self.request.get('minute')
		self.AMPM = self.request.get('AMPM')

		### Validation ###
		email_error = ""
		valid_email = verifyEmail(self.email)
		valid_phone = verifyPhone(self.alert_type, self.phone)
		valid_carrier = verifyCarrier(self.alert_type, self.carrier)

		valid_days = verifyDays(days)
		valid_time = verifyTime(self.hour, self.minute, self.AMPM)
		valid_stations = verifyStations(self.start1, self.start2, self.start3, self.end1, self.end2, self.end3)

		if not (valid_email and valid_phone and valid_carrier and valid_days and valid_time and valid_stations): 
			email_error = ""
			phone_error = ""
			carrier_error = ""
			days_error = ""
			time_error = ""
			start1_error, start2_error, start3_error, end1_error, end2_error, end3_error = "", "", "", "", "", ""
			if valid_email != True:
				email_error = emailError(self.email)
			if valid_phone != True:
				phone_error = phoneError(self.alert_type, self.phone)
			if valid_carrier != True:
				carrier_error = carrierError(self.alert_type, self.carrier)
			if valid_days != True:
				days_error = daysError(days)
			if valid_time != True:
				time_error = timeError(self.hour, self.minute, self.AMPM)
			if valid_stations != True:
				start1_error, start2_error, start3_error, end1_error, end2_error, end3_error = stationsError(self.start1, self.start2, self.start3, self.end1, self.end2, self.end3)
			self.render_alerts_form( 
				email=self.email,
				phone=self.phone,
				carrier=self.carrier,
				start1=self.start1,
				start2=self.start2,
				start3=self.start3,
				end1=self.end1,
				end2=self.end2,
				end3=self.end3,
				email_error=email_error,
				phone_error=phone_error,
				carrier_error=carrier_error,
				start1_error=start1_error,
				start2_error=start2_error,
				start3_error=start3_error,
				end1_error=end1_error,
				end2_error=end2_error,
				end3_error=end3_error,
				hour=self.hour,
				minute=self.minute,
				days_error=days_error,
				time_error=time_error,
				email_sel=self.email_sel,
				text_sel=self.text_sel,
				both_sel=self.both_sel
				)
		else:
			self.done()
	def done(self, *a, **kw):
		raise NotImplementedError

class AlertsPage(AlertsForm):
	def done(self):
		def generate_days():
			candidates=[self.su, self.mo, self.tu, self.we, self.th, self.fr, self.sa]
			finalists=[]
			for c in candidates:
				if c!='':
					c = int(c)
					finalists.append(c)
			return finalists
		days = generate_days()

		def generate_time():
			hour=int(self.hour)
			minute=int(self.minute)
			if hour==12:
				if self.AMPM=='AM':
					hour-=12
			elif self.AMPM=='PM':
				hour+=12
			time=datetime.time(hour, minute, 0)
			return time
		time = generate_time()

		a = Alert(
			email = self.email,
			time = time, 
			days = days
			)
		properties = dict(
			email=self.email, 
			phone=self.phone, 
			carrier=self.carrier, 
			start1=self.start1,
			start2=self.start2,
			start3=self.start3,
			end1=self.end1,
			end2=self.end2,
			end3=self.end3
			)
		for k, v in properties.iteritems():
			if v!='':
				if 'start' in k or 'end' in k or 'phone' in k:
					int_v = int(v)
					setattr(a, k, int_v)
				else:
					setattr(a, k, v)
		a_key = a.put()
		alert_id = a_key.id()
		sendConfirmEmail(
			to=self.email,
			alert_id = alert_id
			)
		self.redirect("/awaitconfirm")

class AwaitConfirmPage(Handler):
	def get(self):
		self.render('awaitconfirm.html')

class EditAlertPage(Handler):
	def get(self):
		self.render('awaitconfirm.html')

class ConfirmAlertPage(Handler):
	def render_confirm_alerts_page(
		self,
		alert_id
		):
		a = Alert.get_by_id(int(alert_id))
		a.confirmed = True
		a.put()

		properties = ['carrier', 'days', 'email', 'end1', 'end2', 'end3', 'phone', 'start1', 'start2', 'start3', 'time']
		values = {}
		for p in properties:
			if getattr(a, p)!=None:
				values[p] = getattr(a, p)
			else:
				values[p] = ''

		email = values['email']
		phone = values['phone']
		carrier = values['carrier']
		start1=values['start1']
		start2=values['start2']
		start3=values['start3']
		end1=values['end1']
		end2=values['end2']
		end3=values['end3']
		days = values['days']
		time = values['time']

		self.render(
			'confirmalerts.html', 
			email=email, 
			phone=phone,
			carrier=carrier,
			start1=start1,
			start2=start2,
			start3=start3,
			end1=end1,
			end2=end2,
			end3=end3,
			days=days,
			time=time,
			alert_id=alert_id
			)
	def get(self, alert_id):
		self.render_confirm_alerts_page(alert_id)

class CancelAlertPage(Handler):
	def render_cancel_alerts_page(
		self,
		alert_id
		):
		a = Alert.get_by_id(int(alert_id))
		a.confirmed = False
		a.put()

		properties = ['carrier', 'days', 'email', 'end1', 'end2', 'end3', 'phone', 'start1', 'start2', 'start3', 'time']
		values = {}
		for p in properties:
			if getattr(a, p)!=None:
				values[p] = getattr(a, p)
			else:
				values[p] = ''

		email = values['email']
		phone = values['phone']
		carrier = values['carrier']
		start1=values['start1']
		start2=values['start2']
		start3=values['start3']
		end1=values['end1']
		end2=values['end2']
		end3=values['end3']
		days = values['days']
		time = values['time']
		
		self.render(
			'cancelalerts.html', 
			email=email, 
			phone=phone,
			carrier=carrier,
			start1=start1,
			start2=start2,
			start3=start3,
			end1=end1,
			end2=end2,
			end3=end3,
			days=days,
			time=time,
			alert_id=alert_id
			)
	def get(self, alert_id):
		self.render_cancel_alerts_page(alert_id)

########## This is where the utils go ##########
##### Email validation #####
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def verifyEmail(email):
	if EMAIL_RE.match(email):
		return True

def emailError(email):
	if not EMAIL_RE.match(email):
		email_error = "That's not a valid email."
		return email_error

##### Phone validation #####
def verifyPhone(alert_type, phone):
	if alert_type=='email':
		return True
	else:
		phone_digitizer = re.compile(r'[^\d]+') #only digits allowed, no other characters
		new_phone = phone_digitizer.sub('', phone)
		if len(str(new_phone))==10:
			return True
def phoneError(alert_type, phone):
	if phone=='':
		if alert_type!='email':
			phone_error = "Phone number field cannot be blank if you've elected to receive text message alerts."
		else:
			phone_error = "Make sure you've elected an email only address, or fill out this field."
	else:
		phone_digitizer = re.compile(r'[^\d]+') #only digits allowed, no other characters
		new_phone = phone_digitizer.sub('', phone)
		print new_phone
		print len(str(new_phone))
		if len(str(new_phone))!=10:
			phone_error="Please enter a valid 10-digit phone number."
		else:
			phone_error="Something else went wrong."
	return phone_error

##### Carrier validation #####
def verifyCarrier(alert_type, carrier):
	if alert_type=='email':
		return True
	else:
		if carrier!='':
			return True

def carrierError(alert_type, carrier):
	if alert_type=='email':
		carrier_error = ''
	elif carrier=='':
		carrier_error = 'Please select your wireless carrier from the list.'
	else:
		carrier_error = 'There was some other kind of error with the carrier selection.'
	return carrier_error

##### Days validation #####
def verifyDays(days):
	if len(days)>0:
		return True

def daysError(days):
	if len(days)==0:
		days_error = 'Select at least one day of the week on which to receive this alert'
	else:
		days_error = 'There was some other error with the days chosen or not chosen'
	return days_error

##### Time validation #####
INTEGER_RE = re.compile(r'[^\d]+')
def verifyTime(hour, minute, AMPM):
	try:
		time=datetime.time(int(hour), int(minute), 0)
		return True
	except:
		print 'invalid time'

def timeError(hour, minute, AMPM):
	if (hour=='' or int(hour)>12 or int(hour<1) or minute=='' or int(minute)>59 or int(minute)<0):
		time_error = 'Please enter valid numbers of hours (1-12) and minutes (0-59).'
	else:
		time_error = 'Please enter a valid time in 12-hour format.'
	return time_error

##### Stations validation ######
def verifyStations(start1, start2, start3, end1, end2, end3):
	stations = [start1, start2, start3, end1, end2, end3]
	#start by making sure that start1 and end1 are filled in
	if (start1!='' and end1!=''):
		#now check for invalid stations
		invalid_stations = 0
		for s in stations:
			if s!='':
				n = StationInfo.query(StationInfo.station_id == int(s)).get()
				if n==None:
					invalid_stations+=1
				else:
					name = n.name
		if invalid_stations==0:
			return True

def stationsError(start1, start2, start3, end1, end2, end3):
	stations = [start1, start2, start3, end1, end2, end3]
	print stations
	errors = ['', '', '', '', '', '']
	print errors
	#first make sure start1 and end1 are populated
	if (start1=='' or end1==''):
		if start1=='':
			errors[0] = 'Select at least one station as your first choice to start from.'
		if end1=='':
			errors[3] = 'Select at least one station as your first choice to dock at the end of your journey.'
	#if the above is not an issue, then move on to checking for stations with invalid IDs
	else:
		i=0
		while i <6:
			if stations[i]!='':
				n = StationInfo.query(StationInfo.station_id == int(stations[i])).get()
				if n==None:
					errors[i]='No station found with this ID.'
			i+=1
	print errors
	return errors[0], errors[1], errors[2], errors[3], errors[4], errors[5]			



