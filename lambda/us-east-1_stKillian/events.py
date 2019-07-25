# ==============================================================================
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
# ==============================================================================
"""Module containing objects that represent events which take place at times."""

__all__ = ["Calendar", "Confession", "Mass"]

# ==============================================================================
# Imports
# ==============================================================================
# stdlib imports
import calendar
import datetime
import pytz

# Amazon imports
import logging

# local imports
import killian_data

# Set up logger object and logging level:
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Calendar(object):
    """Object for managing calendar events like Oktoberfest, etc.
    
    Args:
        userSession (session.KillianUserSession): The current session manager.
    
    """
    def __init__(self, userSession):
        self.userSession = userSession

    def getNextEvents(self, numEvents=3):
        """Asks the datamanager for calendar events this month.
        
        If no events are found for the month, this asks for any events coming
        in the next month.
        
        Args:
            numEvents (int): An optional variable that specifies the number of
                events to fetch. Defaults to 3.

        Returns:
            str, str, str, str, None
            The speech to speak, the reprompt speech to speak after a timeout,
            the title to display on a card, the text to display on a card,
            the cardImage which is None in our case.

        Raises:
            N/A

        """


        dataManager = killian_data.KillianDataManager()
        items = dataManager.getCalendarEvents()
        if not items:
            items = dataManager.getCalendarEvents(monthOffset=1)
        logger.info("items found: {}".format(items))

        if len(items) > numEvents:
            items = items[:numEvents]

        if len(items) == 1:
            phrase = "event is"
        else:
            phrase = "{} events are".format(len(items))

        speech = "The next {}, ".format(phrase)

        for item in items:
            speech += item[0]["eventTitle"]
            speech += ", on "
            eventDate = item[1].strftime("%A, %B %d")
            speech += "{}, ".format(eventDate)
            if "eventTimeEnd" in item[0]:
                eventStartTime = item[1].strftime("%I:%M %p")
                eventEndTime = datetime.datetime(
                    item[0]["eventYear"],
                    item[0]["eventMonth"],
                    item[0]["eventDay"],
                    int(item[0]["eventTimeEnd"].split(":")[0]),
                    int(item[0]["eventTimeEnd"].split(":")[1])
                )
                eventEndTime = eventEndTime.strftime("%I:%M %p")
                speech += "from {} to {}. ".format(eventTime, eventEndTime)
            else:
                eventTime = item[1].strftime("%I:%M %p")
                speech += "at {}. ".format(eventTime)

        reprompt = "What else can I help you with? "
        title = "Upcoming Events"
        text = speech
        cardImage = None
        return speech, reprompt, title, text, cardImage


class Confession(object):
    """Object which forms responses for Confession events."""
    def getNextConfession(self, numEvents=3):
        """Forms the response for confession dates and times.

        Args:
            numEvents (int): An optional variable that specifies the number of
                events to fetch. Defaults to 3.

        Returns:
            str, str, str, str, None
            The speech to speak, the reprompt speech to speak after a timeout,
            the title to display on a card, the text to display on a card,
            the cardImage which is None in our case.

        Raises:
            N/A

        """
        dataManager = killian_data.KillianDataManager()
        items = dataManager.getConfessions()
        logger.info("items found: {}".format(items))

        speech = "The sacrament of reconciliation will be available, "

        for item in items:
            speech += item[0]["dayName"] + ", "
            for timeStr in item[0]["eventTimes"]:
                cTime = datetime.time(
                    int(timeStr.split(",")[0]),
                    int(timeStr.split(",")[1])
                )
                speech += cTime.strftime("%I:%M %p")
                speech += ", "

        speech += "."
        reprompt = "What else can I help you with? "
        title = "Confession"
        text = speech
        cardImage = None
        return speech, reprompt, title, text, cardImage


class Mass(object):
    """Object that forms responses to queries involving Masses.

    Args:
        userSession (session.KillianUserSession): The current session manager.

    """
    def __init__(self, userSession):
        self.userSession = userSession

    def getMassTimeResponse(self, massDay=None):
        """Forms the response for Mass times on a particular day.

        If a day name is not provided, the session is queried for a filled slot
        (indicating the requested day from the user).  If that isn't provided,
        then it falls back to using today's day of the week.

        Adjusts time queries (which come back in UTC) to the local timezone
        which it *assumes* is America/Los_Angeles (a safe assumption given
        the location of the parish).

        Args:
            massDay (str): The name of the day to fetch times for.
                (ex: "Monday") Also supports "Tomorrow" which fetches the next
                day of the week after today, and "Today".

        Returns:
            str, str, str, str, None
            The speech to speak, the reprompt speech to speak after a timeout,
            the title to display on a card, the text to display on a card,
            the cardImage which is None in our case.

        Raises:
            N/A

        """
        targetDay = None
        if not massDay:
            massDay = self.userSession.massDay
        dataManager = killian_data.KillianDataManager()

        if massDay:
            if massDay.endswith("'s"):
                # In case Alexa hears "Friday's mass times"
                massDay = massDay[:-2]
            elif massDay.endswith("s"):
                # In case Alexa hears "Fridays mass times"
                massDay = massDay[:-1]
            todayUtc = datetime.datetime.now(tz=pytz.utc)
            timezone = pytz.timezone("America/Los_Angeles")
            todayLocal = todayUtc.astimezone(timezone)
            today = todayLocal.weekday()
            todayName = calendar.day_name[today]
            if massDay.title() in [todayName, "Today"]:
                targetDay = today
                targetDayName = "Today"
            elif massDay.lower() == "tomorrow":
                targetDay = today + 1
                # Days of the week run 0-6, if we're at 7, that == 0:
                if targetDay > 6:
                    targetDay = 0
                targetDayName = "Tomorrow, {}".format(calendar.day_name[targetDay])
            else:
                targetDayName = massDay
                targetDay = list(calendar.day_name).index(massDay.title())
        else:
            # No mass day provided. Just use today.
            todayUtc = datetime.datetime.now(tz=pytz.utc)
            timezone = pytz.timezone("America/Los_Angeles")
            todayLocal = todayUtc.astimezone(timezone)
            targetDay = todayLocal.weekday()
            targetDayName = "Today"

        # Grab the times from the database:
        times = dataManager.getMassTimes(targetDay)

        if not times:
            speech = "There are no masses on {}. ".format(targetDayName)
        else:
            timeString = ""
            #for massTime, language in times:
            for massTime, language in times:
                if timeString:
                    timeString += ", "
                timeString += convertMassToString(massTime, language=language)
            speech = "{}, the mass times are {}.".format(targetDayName, timeString)

        reprompt = "Try asking: when is the next Mass."
        title = "Mass Times: {}".format(targetDayName)
        text = "{} mass times:\n{}".format(targetDayName, timeString)
        cardImage = None
        return speech, reprompt, title, text, cardImage

    def getNextMass(self):
        dataManager = killian_data.KillianDataManager()
        today = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        todayLocal = today.astimezone(timezone)
        todayNum = todayLocal.weekday()
        times = dataManager.getMassTimes(todayNum)
        if not times:
            return None
        lastMassTime = times[-1][0]
        nowTime = todayLocal.time()
        logger.info("Mass today?({}), at {}".format(todayNum, nowTime))
        if nowTime > lastMassTime:
            logger.info("No more masses today({}), at {}".format(todayNum, nowTime))
            return None
        i = 0
        bestMass = times[i][0]
        while nowTime > bestMass:
            i += 1
            bestMass = times[i][0]
            language = times[i][1]
        print("-- Chosen Mass {}".format(bestMass))
        return {"time": bestMass, "language": language}

    def getNextMassResponse(self):
        speech = ""
        nextMass = self.getNextMass()
        if not nextMass:
            logger.info("No more masses today.")
            speech += "There are no more masses today. "
            tSpeech, reprompt, _, _, _ = self.getMassTimeResponse(
                massDay="tomorrow"
            )
            speech += tSpeech
        else:
            i = 0
            bestMass = nextMass["time"]
            language = nextMass["language"]
            massString = convertMassToString(bestMass, language=language)
            speech = "The next mass today will be at {}".format(massString)
            reprompt = "What else can I do for you?"
        title = "Next Mass"
        text = speech
        cardImage = None
        return speech, reprompt, title, text, cardImage


# =============================================================================
# Functions
# =============================================================================
def convertMassToString(massTime, language="english"):
    hour = massTime.hour
    if hour > 11:
        suffix = "pm"
    else:
        suffix = "am"
    if not language.lower() == "english":
        suffix += " in {}".format(language)
    if hour > 12:
        hour = hour - 12
    minute = "{:02d}".format(massTime.minute)
    return "{}:{} {}".format(hour, minute, suffix)
