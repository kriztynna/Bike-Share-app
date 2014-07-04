########## This is where the database models go ##########

from google.appengine.ext import ndb


class StationInfo(ndb.Model):
	station_id = ndb.IntegerProperty(required=True)
	name = ndb.StringProperty(required=True)
	coordinates = ndb.GeoPtProperty(required=True)
	stAddress1 = ndb.StringProperty(required=True)
	stAddress2 = ndb.StringProperty(required=False)


class StationStatus(ndb.Model):
	station_id = ndb.IntegerProperty(required=True)
	availableDocks = ndb.IntegerProperty(required=True)
	totalDocks = ndb.IntegerProperty(required=True)
	statusKey = ndb.IntegerProperty(required=True)
	availableBikes = ndb.IntegerProperty(required=True)
	date_time = ndb.DateTimeProperty(required=True)
	errors = ndb.IntegerProperty(required=True)

	@classmethod
	def by_id(cls, sid):
		status = StationStatus.query(StationStatus.station_id == sid).get()
		return status


class StatusInfo(ndb.Model):
	statusValue = ndb.StringProperty(required=True)
	statusKey = ndb.IntegerProperty(required=True)


class Totals(ndb.Model):
	date_time = ndb.DateTimeProperty(required=True)
	bikes = ndb.IntegerProperty(required=True)
	docks = ndb.IntegerProperty(required=True)
	errors = ndb.IntegerProperty(required=True)


class SystemStats(ndb.Model):
	date = ndb.DateProperty(required=True)
	trips = ndb.IntegerProperty(required=True) #5pm to #5pm
	miles = ndb.IntegerProperty(required=True) #5pm to 5pm
	miles_per_trip = ndb.FloatProperty(required=True)
	cum_trips = ndb.IntegerProperty(required=True) #since launch
	cum_miles = ndb.IntegerProperty(required=True) #since launch
	signups = ndb.IntegerProperty(required=True) #annual pass
	members = ndb.IntegerProperty(required=True) #annual pass
	day_passes = ndb.IntegerProperty(required=False) #5pm to 5pm
	week_passes = ndb.IntegerProperty(required=False) #5pm to 5pm


class Alert(ndb.Model):
	email = ndb.StringProperty(required=False)

	phone = ndb.IntegerProperty(required=False)
	carrier = ndb.StringProperty(required=False)

	start1 = ndb.IntegerProperty(required=False)
	start2 = ndb.IntegerProperty(required=False)
	start3 = ndb.IntegerProperty(required=False)

	end1 = ndb.IntegerProperty(required=False)
	end2 = ndb.IntegerProperty(required=False)
	end3 = ndb.IntegerProperty(required=False)

	time = ndb.TimeProperty(required=True)

	# List of integers representing day of the week.
	# As the convention in Python, 0 is Sunday and 6 is Saturday.
	days = ndb.IntegerProperty(repeated=True)

	confirmed = ndb.BooleanProperty(default=False)


class AlertLog(ndb.Model):
	alert_id = ndb.IntegerProperty(required=False)
	email = ndb.StringProperty(required=False)

	phone = ndb.IntegerProperty(required=False)
	carrier = ndb.StringProperty(required=False)

	start1 = ndb.IntegerProperty(required=False)
	start2 = ndb.IntegerProperty(required=False)
	start3 = ndb.IntegerProperty(required=False)

	end1 = ndb.IntegerProperty(required=False)
	end2 = ndb.IntegerProperty(required=False)
	end3 = ndb.IntegerProperty(required=False)

	time = ndb.TimeProperty(required=True)

	complete = ndb.BooleanProperty(required=True, default=False)
	sent = ndb.DateTimeProperty(required=False)




