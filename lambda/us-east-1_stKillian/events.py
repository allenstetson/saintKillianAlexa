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
import logging
import pytz

# local imports
import killian_data

# Set up LOGGER object and logging level:
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class Calendar:
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
        LOGGER.info("items found: {}".format(items))

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


class Confession:
    """Object which forms responses for Confession events."""
    def getNextConfession(self):
        """Forms the response for confession dates and times.

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
        LOGGER.info("items found: {}".format(items))

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


class Mass:
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
                targetDayName = "Tomorrow, {}".format(
                    calendar.day_name[targetDay]
                )
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
            speech = "{}, the mass times are {}.".format(
                targetDayName,
                timeString
            )

        reprompt = "Try asking: when is the next Mass."
        title = "Mass Times: {}".format(targetDayName)
        text = "{} mass times:\n{}".format(targetDayName, timeString)
        cardImage = None
        return speech, reprompt, title, text, cardImage

    def getNextMass(self):
        """Gets the first mass that takes place today after now.

        This assumes a timezone of America/Los_Angeles (a safe assumption
        given the location of the parish).

        Returns:
            dict or None
            If there are no masses, this returns None; otherwise it returns a
            the chosen Mass along with the language that it will be given in.

        """
        dataManager = killian_data.KillianDataManager()
        today = datetime.datetime.now(tz=pytz.utc)
        timezone = pytz.timezone("America/Los_Angeles")
        todayLocal = today.astimezone(timezone)
        todayNum = todayLocal.weekday()
        times = dataManager.getMassTimes(todayNum)
        if not times:
            # No Masses take place on this day at all.
            return None
        # Grab the last mass and compare it to now. If it's after now, then we
        #  are too late -- we've missed all of the Masses today.
        lastMassTime = times[-1][0]
        nowTime = todayLocal.time()
        LOGGER.info("Mass today?({}), at {}".format(todayNum, nowTime))
        if nowTime > lastMassTime:
            LOGGER.info("No more masses today({}), at {}".format(
                todayNum, nowTime
            ))
            return None

        # Iterate through the Masses looking for the first one that is after
        #  now.
        i = 0
        bestMass = times[i][0]
        while nowTime > bestMass:
            i += 1
            bestMass = times[i][0]
            language = times[i][1]
        print("-- Chosen Mass {}".format(bestMass))
        return {"time": bestMass, "language": language}

    def getNextMassResponse(self):
        """Forms a proper response for asking for the next mass today.

        Returns:
            str, str, str, str, None
            The speech to speak, the reprompt speech to speak after a timeout,
            the title to display on a card, the text to display on a card,
            the cardImage which is None in our case.

        Raises:
            N/A

        """
        speech = ""
        nextMass = self.getNextMass()
        if not nextMass:
            LOGGER.info("No more masses today.")
            speech += "There are no more masses today. "
            tSpeech, reprompt, _, _, _ = self.getMassTimeResponse(
                massDay="tomorrow"
            )
            speech += tSpeech
        else:
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
    """Formats a mass time into a readable string.

    Most of this can be replaced with strftime formatting for %I and %p.
    The only real useful part of this is the language handling.

    Args:
        massTime (datetime.datetime): The datetime of the Mass.
        language (str): Optional, the language that the mass will be given in.
        (Defaults to "english")

    """
    hour = massTime.hour
    if hour > 11:
        suffix = "pm"
    else:
        suffix = "am"
    if language.lower() != "english":
        suffix += " in {}".format(language)
    if hour > 12:
        hour = hour - 12
    minute = "{:02d}".format(massTime.minute)
    return "{}:{} {}".format(hour, minute, suffix)
