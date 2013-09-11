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
from google.appengine.api import mail

def sendEmail(
    to='',
    start1_name='',
    start1_bikes='',
    start1_time='',
    end1_name='',
    end1_docks='',
    end1_time=''
    ):

    body = '%(start1_name)s at %(start1_time)s \n\
Bikes: %(start1_bikes)d \n\n\
%(end1_name)s at %(end1_time)s\n\
Docks: %(end1_docks)d \n\n\
enjoy your journey!\n\n\
-busybici' % \
            {'start1_time':start1_time, \
            'start1_bikes':start1_bikes, \
            'start1_name':start1_name, \
            'end1_time':end1_time, \
            'end1_docks':end1_docks, \
            'end1_name':end1_name}

    message = mail.EmailMessage(
        sender='busybici <busybici@bikeshareapp.appspotmail.com>',
        subject='busybici update',
        to=to,
        body=body
        )
    message.send()

def sendSMS(
    to='',
    start1_name='',
    start1_bikes='',
    start1_time='',
    end1_name='',
    end1_docks='',
    end1_time=''
    ):

    body = '%(start1_name)s %(start1_time)s \n\
Bikes: %(start1_bikes)d \n\
%(end1_name)s %(end1_time)s\n\
Docks: %(end1_docks)d' % \
            {'start1_time':start1_time, \
            'start1_bikes':start1_bikes, \
            'start1_name':start1_name, \
            'end1_time':end1_time, \
            'end1_docks':end1_docks, \
            'end1_name':end1_name}

    message = mail.EmailMessage(
        sender='busybici <busybici@bikeshareapp.appspotmail.com>',
        subject='',
        to=to,
        body=body
        )
    message.send()

def distribute(
    entity='',
    start1_name='',
    start1_bikes='',
    start1_time='',
    end1_name='',
    end1_docks='',
    end1_time=''
    ):
    if entity['email']!=None:
        sendEmail(
            to=entity['email'],
            start1_name=start1_name,
            start1_bikes=start1_bikes,
            start1_time=start1_time,
            end1_name=end1_name,
            end1_docks=end1_docks,
            end1_time=end1_time
            )
    if entity['phone']!=None:
        to = str(entity['phone'])+carriers[entity['carrier']]
        sendSMS(
            to=to,
            start1_name=start1_name,
            start1_bikes=start1_bikes,
            start1_time=start1_time,
            end1_name=end1_name,
            end1_docks=end1_docks,
            end1_time=end1_time
            )

def generate_msg_info(
    entity
    ):

    start1=entity['start1']
    start1_status = StationStatus.query(StationStatus.station_id==start1).order(-StationStatus.date_time).get()
    start1_bikes = start1_status.availableBikes
    start1_time = start1_status.date_time
    start1_time = convertTime(start1_time)
    start1_info = StationInfo.query(StationInfo.station_id==start1).get()
    start1_name = start1_info.name

    end1=entity['end1']
    end1_status = StationStatus.query(StationStatus.station_id==end1).order(-StationStatus.date_time).get()
    end1_docks = end1_status.availableDocks
    end1_time = end1_status.date_time
    end1_time = convertTime(end1_time)
    end1_info = StationInfo.query(StationInfo.station_id==end1).get()
    end1_name = end1_info.name

    distribute(
        entity=entity,
        start1_name=start1_name,
        start1_bikes=start1_bikes,
        start1_time=start1_time,
        end1_name=end1_name,
        end1_docks=end1_docks,
        end1_time=end1_time
        )

def work_thru_todays_list(
    todays_list=None
    ):
    
    todays_list_len = len(todays_list)

    if todays_list_len==0:
        logging.debug('Done for the day. See you tomorrow.')
    else:
        while len(todays_list) > 0:
            a = todays_list[0]
            now = makeNowTime()
            if a['time']<=now:
                generate_msg_info(a)
                logging.debug(
                    'I sent an alert that was scheduled for %s.',
                    a['time'].strftime('%I:%M %p')
                    )
                todays_list.remove(a)
            else:
                next_time = (a['time'].hour*3600)+(a['time'].minute*60)+a['time'].second
                now_seconds = (now.hour*3600)+(now.minute*60)+now.second
                wait = next_time - now_seconds
                logging.debug(
                    'Next alert will go out in %d seconds. Going to sleep until then.',
                    wait
                    )
                time.sleep(wait)
                break

        deferred.defer(
            work_thru_todays_list,
            todays_list=todays_list,
            _queue="sendthealerts"
            )

class CreateAlerts(webapp2.RequestHandler):
    def create_records(self):
        alert = Alert(
            email='cristina.colon@gmail.com', 
            start1=357, 
            end1=327,
            time=datetime.time(20, 0, 0)
            )
        alert.put()
        alert2 = Alert(
            email='cristina.colon@gmail.com',
            start1=293,
            end1=426,
            time=datetime.time(21, 0, 0)
            )
        alert2.put()
        alert3 = Alert( 
            email='cristina.colon@gmail.com', 
            start1=483, 
            end1=147,
            time=datetime.time(21, 15, 0)
            )
        alert3.put()
    def get(self):
        self.create_records()


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

    # make the now, convert to new york time
    n = datetime.datetime.now()
    n = utc.localize(n)
    n = n.astimezone(newyork)

    # reduce to just the time in HH:MM:SS
    n = n.time()
    n = n.replace(microsecond=0)
    return n

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