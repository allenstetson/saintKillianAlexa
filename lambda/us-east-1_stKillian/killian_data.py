# ==============================================================================
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
# ==============================================================================
"""Module with data manager which interacts with a database upon request."""

__all__ = ["KillianDataManager"]

# ==============================================================================
# Imports
# ==============================================================================
# stdlib imports
import datetime
import logging
import pytz

# Amazon imports
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Set up LOGGER object and logging level:
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# ==============================================================================
# Classes
# ==============================================================================
class KillianDataManager(object):
    """Data broker that writes and reads data to/from database.

    Uses dynamodb as the main database, in the us-east-1 region, table name:
    StKillian

    """
    def __init__(self):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            endpoint_url="http://dynamodb.us-east-1.amazonaws.com"
        )
        self.dbTable = self.dynamodb.Table("StKillian")

    def getCalendarEvents(self, monthOffset=0):
        """Gets upcoming calendar events for this month.

        Args:
            monthOffset (int): An offset number to add to the current month
                in case you want to query for next month (1) or the previous
                month (-1), etc.

        Returns:
            [(dict, datetime.datetime)]
            A list of tuples containing the item found along with its datetime.

        """
        msg = "Attempting to retrieve calendar events from db"
        LOGGER.info(msg)

        nowUtc = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        now = nowUtc.astimezone(timezone)

        # Apply the month offset, if any. If the offset takes it out of 1-12,
        #  repair that number (so -2 should equal 10 - October).
        month = now.month
        month += monthOffset
        if month > 12:
            month = month - 12
        elif month < 1:
            month = month + 12

        # Query the database
        #  NOTE: the 'scan' operation in dynamodb is expensive. If the DB ever
        #  grows to a very large size (10k+), this will be a bad solution.
        #  However, more elegant solutions rely on knowing the keyname of the
        #  DB entry which is impossible in our current schema.
        items = []
        try:
            fe = Key("eventCategory").eq("calendar") & \
                 Key("eventYear").eq(now.year) & \
                 Key("eventMonth").eq(month)
            response = self.dbTable.scan(
                FilterExpression=fe,
            )
            LOGGER.info("response: {}".format(response))
            # If nothing is found:
            if response['Count'] == 0:
                LOGGER.info("No items found for query.")
                return []
            # Store found items:
            items = response['Items']
        # If the DB query raises an error:
        except ClientError as e:
            LOGGER.info("query for calendar events failed.")
            LOGGER.error(e.response['Error']['Message'])
            return []

        # Good, we've made it through the query. Now derive the datetime from
        #  the stored values, and save this for returning.
        found = []
        for item in items:
            eventDatetime = datetime.datetime(
                item["eventYear"],
                item["eventMonth"],
                item["eventDay"],
                int(item["eventTimeStart"].split(":")[0]),
                int(item["eventTimeStart"].split(":")[1])
            )
            if now > eventDatetime:
                continue
            found.append((item, eventDatetime))
        # Sort based on datetime and return.
        found = sorted(found, key=lambda x: x[1])
        return found

    def getConfessions(self):
        """Gets confession times by day of week.

        Returns:
            [(dict, int)]
            A list of tuples containing the item found along with a sort order
            based on today's day of week enum in relation to the item. (This
            ensures that the next upcoming item is reported first, even if it
            is a higher enum number than, say, a Monday).

        """
        msg = "Attempting to retrieve confessions from db"
        LOGGER.info(msg)

        nowUtc = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        now = nowUtc.astimezone(timezone)

        # Query the database
        #  NOTE: the 'scan' operation in dynamodb is expensive. If the DB ever
        #  grows to a very large size (10k+), this will be a bad solution.
        #  However, more elegant solutions rely on knowing the keyname of the
        #  DB entry which is impossible in our current schema.
        items = []
        try:
            fe = Key("eventCategory").eq("confession")
            response = self.dbTable.scan(
                FilterExpression=fe,
            )
            LOGGER.info("response: {}".format(response))
            # If no items are found:
            if response['Count'] == 0:
                LOGGER.info("No items found for query.")
                return []
            # Store found items
            items = response['Items']
        # If DB query raises an error:
        except ClientError as e:
            LOGGER.info("query for confession failed.")
            LOGGER.error(e.response['Error']['Message'])
            return []

        # Good, we found some items. Format them for return.
        found = []
        for item in items:
            if item["dayEnum"] < now.weekday():  # This day already passed
                # Since this day of the week already passed, let's increase
                #  its sort order so that it now comes in the future. (Last
                #  Monday becomes next Monday)
                order = item["dayEnum"] + 7
            else:
                order = item["dayEnum"]
            found.append((item, order))
        # Sort based on sort order (modified day of week enum) and return:
        found = sorted(found, key=lambda x: x[1])
        return found

    def getHolyDayByDate(self, requestedDate):
        """Get Holy Day by a calendar date.

        Returns:
            dict
                The data for a holy day matching the requested date.

        """
        msg = "Attempting to retrieve holy days from db"
        LOGGER.info(msg)

        nowUtc = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        now = nowUtc.astimezone(timezone)
        targetDate = requestedDate.replace(year=now.year)

        # Query the database
        #  NOTE: the 'scan' operation in dynamodb is expensive. If the DB ever
        #  grows to a very large size (10k+), this will be a bad solution.
        #  However, more elegant solutions rely on knowing the keyname of the
        #  DB entry which is impossible in our current schema.
        items = []
        try:
            filterExp = Key("eventCategory").eq("holyday")
            response = self.dbTable.scan(
                FilterExpression=filterExp,
            )
            LOGGER.info("response: {}".format(response))
            # If no items are found:
            if response['Count'] == 0:
                LOGGER.info("No items found for query.")
                return []
            # Store found items
            items = response['Items']
        # If DB query raises an error:
        except ClientError as e:
            LOGGER.info("query for holy day by date failed.")
            LOGGER.error(e.response['Error']['Message'])
            return []

        # Good, we found some items. Cross reference the target date:
        for item in items:
            year = item.get("eventYear", 1976)
            month = item.get("eventMonth", 11)
            day = item.get("eventDay", 15)
            thisEventDate = datetime.date(year, month, day)
            if thisEventDate == targetDate:
                return item
        return {}

    def getHolyDayByEnum(self, dayEnum):
        """Gets mass times for a specific day of the week.

        Args:
            dayEnum (int): The number representing the day of the week for
                which we want mass times.

        Returns:
            [(datetime.time, str)]
            List of tuples containing the time that the mass takes place
                along with the name of the language that the Mass will be
                given in.

        """
        msg = "Attempting to retrieve holy day mass times for {} from db"
        msg = msg.format(dayEnum)
        LOGGER.info(msg)

        # Assemble the primary key for quick DB retrieval
        namespace = "event:mass:holyday:{}".format(dayEnum)

        # Query the database
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            # If the item is not found:
            if not 'Item' in response:
                return None

            # Store the item
            item = response['Item']
        # If the database query raises an error:
        except ClientError as e:
            LOGGER.info("get_item for mass times failed.")
            LOGGER.error(e.response['Error']['Message'])
            return None

        # Good, we found the event. Find times, format them for return
        return item

    def getHolyDayMassTimesByEnum(self, dayEnum):
        """Gets mass times for a specific day of the week.

        Args:
            dayEnum (int): The number representing the day of the week for
                which we want mass times.

        Returns:
            [(datetime.time, str)]
            List of tuples containing the time that the mass takes place
                along with the name of the language that the Mass will be
                given in.

        """
        msg = "Attempting to retrieve holy day mass times for {} from db"
        msg = msg.format(dayEnum)
        LOGGER.info(msg)

        # Assemble the primary key for quick DB retrieval
        namespace = "event:mass:holyday:{}".format(dayEnum)

        # Query the database
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            # If the item is not found:
            if not 'Item' in response:
                return None

            # Store the item
            item = response['Item']
        # If the database query raises an error:
        except ClientError as e:
            LOGGER.info("get_item for mass times failed.")
            LOGGER.error(e.response['Error']['Message'])
            return None

        # Good, we found the event. Find times, format them for return
        #FIXME: Must check for valid holy day times first!:
        if item.get("eventTimes"):
            times = list()
            for massString in item['eventTimes']:
                if len(massString.split(",")) == 2:
                    hourNum, minNum = massString.split(",")
                    language = "english"
                else:
                    hourNum, minNum, language = massString.split(",")

                times.append((datetime.time(int(hourNum), int(minNum)), language))
            # Sort them based on the time and return
            times = sorted(times, key=lambda x: x[0].hour)
            return times

        # A holy day, it may not have times associated.
        #  If this is the case, we'll need to fall back on the day
        #  of the week on which it falls.
        #  If this is not defined, we'll need to report that these
        #  times have not yet been defined.

        # Get datetime. Use my birthday as a default since I'm so old
        year = item.get("eventYear", 1976)
        month = item.get("eventMonth", 11)
        day = item.get("eventDay", 15)
        eventDate = datetime.date(year, month, day)

        todayUtc = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        todayLocal = todayUtc.astimezone(timezone)

        if eventDate < todayLocal.date():
            # This item is in the past
            #  This means that we can't rely on its date information.
            #  We're essentially flying blind here, and the best that we can do
            #  is to report that this holy day hasn't been set up yet.
            return None

        # This event has a date, but not mass times. Just return the times for
        #  that day.
        dayEnum = eventDate.weekday()
        return self.getMassTimesByEnum(dayEnum)

    def getMassTimesByEnum(self, dayEnum):
        """Gets mass times for a specific day of the week.

        Args:
            dayEnum (int): The number representing the day of the week for
                which we want mass times.

        Returns:
            [(datetime.time, str)]
            List of tuples containing the time that the mass takes place
                along with the name of the language that the Mass will be
                given in.

        """
        msg = "Attempting to retrieve mass times for {} from db"
        msg = msg.format(dayEnum)
        LOGGER.info(msg)

        # Assemble the primary key for quick DB retrieval
        namespace = "event:mass:daily:{}".format(dayEnum)

        # Query the database
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            # If the item is not found:
            if not 'Item' in response:
                return None

            # Store the item
            item = response['Item']
        # If the database query raises an error:
        except ClientError as e:
            LOGGER.info("get_item for mass times failed.")
            LOGGER.error(e.response['Error']['Message'])
            return None

        # Good, we found some times. Format them for return
        times = list()
        for massString in item['eventTimes']:
            if len(massString.split(",")) == 2:
                hourNum, minNum = massString.split(",")
                language = "english"
            else:
                hourNum, minNum, language = massString.split(",")

            times.append((datetime.time(int(hourNum), int(minNum)), language))
        # Sort them based on the time and return
        times = sorted(times, key=lambda x: x[0].hour)
        return times

    def getParishOfficePhoneNumber(self):
        """Gets the parish office phone number from the database.

        Returns:
            int: The phone number as a 9 digit integer.

        """
        msg = "Attempting to retrieve parish office phone number from db"
        LOGGER.info(msg)

        # Use the known primary key for fast DB retrieval:
        namespace = "info:office:phone"

        # Query the Database
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            # If no item found:
            if not 'Item' in response:
                return None

            # Store the item
            item = response['Item']
        # If the database query raises an error:
        except ClientError as e:
            LOGGER.info("get_item for parish office phone failed.")
            LOGGER.error(e.response['Error']['Message'])
            return None

        # return the number from the item:
        return item['phoneNumber']

    def getUserDatabaseEntry(self, userId):
        """Pulls a user record from the database based on userId.

        This is used for persistent attributes across sessions, notably,
        AudioPlayer tokens and tracks.  User preferences may also be stored
        here some day.

        Args:
            userId (str): The Amazon user id token of the current user.

        Returns:
            dict: The entire user db entry.

        """
        msg = "Attempting to find user entry for userId..."
        LOGGER.info(msg)

        # Query the database
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': userId}
            )
            # If no record found, this is a new user; return empty dict:
            if not "Item" in response:
                LOGGER.info("New user!")
                return {}

            # Store the found entry:
            item = response['Item']
        # If the database query raises an error:
        except ClientError as e:
            LOGGER.info("get_item for userId failed.")
            LOGGER.error(e.response['Error']['Message'])
            return None

        # Return that entry in its entirety:
        return item

    def updateUserDatabaseEntry(self, userId, dbEntry):
        """Writes a user database entry to the database.

        Args:
            userId (str): The Amazon user id token of the current user.
            dbEntry (dict): The user information to write to the DB.

        Returns:
            bool: Whether or not we met with success.

        """
        msg = "Attempting to write user data..."
        LOGGER.info(msg)

        # Derive the update expression for storing values
        #  This is Amazon's way of making this DB query secure from injection
        #  attacks:
        updateExpression = "set lastToken=:o, lastTrack=:k, "
        updateExpression += "offsetInMilliseconds=:f"

        # Update the database
        try:
            self.dbTable.update_item(
                TableName="StKillian",
                Key={"namespace": userId},
                UpdateExpression=updateExpression,
                ExpressionAttributeValues={
                    ":o": dbEntry.get("lastToken", ""),
                    ":k": dbEntry.get("lastTrack", ""),
                    ":f": dbEntry.get("offsetInMilliseconds", 0)
                },
                ReturnValues="UPDATED_NEW"
            )
            return True
        # If the update raised an error:
        except ClientError as e:
            LOGGER.info("ClientError received!")
            LOGGER.error(e.response["Error"]["Message"])
            return False
