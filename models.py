########## This is where the database models go ##########

from google.appengine.ext import ndb

class StationInfo(ndb.Model):
        station_id = ndb.IntegerProperty(required = True)
        name = ndb.StringProperty(required = True)
        coordinates = ndb.GeoPtProperty(required = True)
        stAddress1 = ndb.StringProperty(required = True)
        stAddress2 = ndb.StringProperty(required = False)

class StationStatus(ndb.Model):
        station_id = ndb.IntegerProperty(required = False)
        availableDocks = ndb.IntegerProperty(required = False)
        totalDocks = ndb.IntegerProperty(required = False)
        statusKey = ndb.IntegerProperty(required = False)
        availableBikes = ndb.IntegerProperty(required = False)
        date_time = ndb.DateTimeProperty(required = False)
        errors = ndb.IntegerProperty(required = False)

        @classmethod
	def by_id(cls, sid):
                status = StationStatus.query(StationStatus.station_id == sid).get()
		return status

class StatusInfo(ndb.Model):
        statusValue = ndb.StringProperty(required = True)
        statusKey = ndb.IntegerProperty(required = True)

class Totals(ndb.Model):
        date_time = ndb.DateTimeProperty(required = True)
        bikes = ndb.IntegerProperty(required = True)
        docks = ndb.IntegerProperty(required = True)
        errors = ndb.IntegerProperty(required = True)