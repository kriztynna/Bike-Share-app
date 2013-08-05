########## This is where the database models go ##########

from google.appengine.ext import db

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
        errors = db.IntegerProperty(required = True)

        @classmethod
	def by_id(cls, sid):
                status = StationStatus.all().filter('station_id =', sid).get()
		return status

class StatusInfo(db.Model):
        statusValue = db.StringProperty(required = True)
        statusKey = db.IntegerProperty(required = True)

class Totals(db.Model):
        date_time = db.DateTimeProperty(required = True)
        bikes = db.IntegerProperty(required = True)
        docks = db.IntegerProperty(required = True)
        errors = db.IntegerProperty(required = True)