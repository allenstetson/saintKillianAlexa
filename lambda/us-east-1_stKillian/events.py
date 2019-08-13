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
import random

# external imports
import pytz

# amazon imports
from ask_sdk_model.interfaces.audioplayer import (
    PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata,
    StopDirective, AudioPlayerState)
from ask_sdk_model.ui.image import Image

# local imports
import killian_data

# Set up LOGGER object and logging level:
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


# ==============================================================================
# Classes
# ==============================================================================
class Calendar:
    """Object for managing calendar events like Oktoberfest, etc.

    Args:
        userSession (session.KillianUserSession): The current session manager.

    """
    def __init__(self, userSession):
        self.userSession = userSession

    def getNotImplementedResponse(self):
        """Plays an audio announcement that this feature is forthcoming.

        Until a shared calendar is in place, I cannot look up calendar events.
        So that the user knows that this feature is coming, this plays a nice
        song with a happy announcer telling the user that the feature is on
        its way.

        Args:
            N/A

        Raises:
            N/A

        Returns:
            str, str, str, ask_sdk_model.interfaces.audioplayer.PlayDirective, dict
            The speech for Alexa to speak,
            the title to display on the card,
            the text to display on the card,
            the play directive telling Alexa what audio file to play,
            session attributes to be passed to Alexa.

        """
        url = "https://st-killian-resources.s3.amazonaws.com/calendarGeneric_mixdown.mp3"
        token = "calendarGeneric_mixdown"
        speech = ""
        title = "St. Killian calendar events"
        text = "Calendar events coming soon! Watch the bulletin for news."
        self.userSession.lastToken = token
        self.userSession.lastTrack = url
        self.userSession.savePersistentAttrs()

        sessionAttrs = {
            "lastTrack": url,
            "lastToken": token
        }
        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    expected_previous_token=None,
                    token=token,
                    url=url,
                    offset_in_milliseconds=0
                ),
                metadata=AudioItemMetadata(
                    title="Calendar Events",
                    subtitle=text
                )
            )
        )
        return speech, title, text, directive, sessionAttrs

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

# =============================================================================

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

# =============================================================================

class HolyDays:
    """Holy day names and enums, used for checking mass times."""
    index = {
        100: ["solemnity of mary"],
        101: ["solemnity of the epiphany of the lord", "epiphany of the lord",
              "epiphany", "feast of the epiphany"],
        102: ["baptism of the lord"],
        103: ["ash wednesday"],
        104: ["solemnity of saint joeseph", "feast of saint joeseph"],
        105: ["solemnity of the annunciation of the lord", "annunciation",
              "annunciation of the lord", "feast of the annunciation"],
        106: ["palm sunday"],
        107: ["holy thursday"],
        108: ["good friday"],
        109: ["holy saturday"],
        110: ["easter", "easter sunday"],
        111: ["divine mercy sunday"],
        112: ["ascension of the lord", "ascension"],
        113: ["pentecost", "pentecost sunday"],
        114: ["solemnity of the most holy trinity", "holy trinity",
              "solemnity of the holy trinity", "feast of the holy trinity"],
        115: ["solemnity of the most holy body and blood of christ",
              "corpus christi", "solemnity of the body and blood of christ",
              "solemnity of the body and blood", "feast of corpus christi",
              "feast of the body and blood"],
        116: ["solemnity of the nativity of saint john the baptist",
              "solemnity of the nativity of john the baptist",
              "solemnity of saint john the baptist",
              "solemnity of john the baptist", "feast of john the baptist"],
        117: ["solemnity of the most sacred heart of jesus",
              "solemnity of the sacred heart", "feast of the sacred heart",
              "sacred heart of jesus", "sacred heart"],
        118: ["solemnity of saints peter and paul", "feast of saint peter",
              "solemnity of peter and paul", "feast of saint paul",
              "feast of the apostles", "solemnity of the apostles"],
        119: ["solemnity of the assumption of the blessed virgin mary",
              "solemnity of the assumption of mary", "feast of the assumption",
              "solemnity of the assumption", "assumption of mary",
              "assumption of the virgin mary", "assumption of the virgin",
              "assumption"],
        120: ["all saints day"],
        121: ["all souls day", "commemoration of all the faithful departed",
              "commemoration of all of the faithfully departed"],
        122: ["solemnity of our lord jesus christ king of the universe",
              "feast of christ the king", "solemnity of christ the king",
              "solemnity of our lord jesus", "solemnity of jesus christ",
              "solemnity of our lord jesus christ", "solemnity of christ",
              "solemnity of jesus"],
        123: ["solemnity of the immaculate conception of the blessed virgin mary",
              "solemnity of the immaculate conception", "immaculate conception",
              "feast of the immaculate conception",
              "feast of the immaculate conception of mary",
              "feast of the immaculate conception of the virgin mary"],
        124: ["christmas", "nativity of the lord", "christmas day",
              "christmas eve"]
    }

    def isHolyDay(self, inputWords):
        """Checks to see if the words spoken correspond to a holy day."""
        match = [x for x in self.index if inputWords.lower() in self.index[x]]
        if match:
            return True
        return False

    def getHolyDayEnumByName(self, name):
        """Given a holy day name, fetch the corresponding enum value."""
        match = [x for x in self.index if name.lower() in self.index[x]]
        if not match:
            return None
        return match[0]

    def getHolyDayNameByEnum(self, enum):
        """Given a number, match that with a holy day name."""
        if not enum in self.index:
            return None
        name = self.index[enum][0]
        if name.startswith("solemnity") or name.startswith("ascension") or \
                name.startswith("baptism"):
            name = "the " + name
        return name

# =============================================================================

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
            targetDay, targetDayName = self.resolveMassDay(massDay)
            if not targetDay:
                speech = "I'm not sure that I understood your question. "
                speech += "Can you ask again? "
                timeString = "Try asking again..."
                targetDayName = "Unsure"
                reprompt = "Try asking again. "
                title = "I must have misheard you."
                text = "Please ask again."
                return speech, reprompt, title, text, None
        else:
            # No mass day provided. Just use today.
            todayUtc = datetime.datetime.now(tz=pytz.utc)
            timezone = pytz.timezone("America/Los_Angeles")
            todayLocal = todayUtc.astimezone(timezone)
            targetDay = todayLocal.weekday()
            targetDayName = "Today"

        # Grab the times from the database:
        if targetDay >= 100:
            times = dataManager.getHolyDayMassTimesByEnum(targetDay)
        else:
            times = dataManager.getMassTimesByEnum(targetDay)

        if not times:
            speech = "Masses have not yet been defined for {}. "
            speech += "Please check back later for more information. "
            speech = speech.format(targetDayName)
            timeString = "No masses yet defined."
        else:
            timeString = ""
            for massTime, language in times:
                if timeString:
                    timeString += ", "
                timeString += convertMassToString(massTime, language=language)
            speeches = []
            speeches.append("{}, the mass times are {}.".format(
                targetDayName,
                timeString
            ))
            speeches.append("The mass times for {} are {}.".format(
                targetDayName,
                timeString
            ))
            speech = random.choice(speeches)

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
        times = dataManager.getMassTimesByEnum(todayNum)
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
        cardImage = Image(
            small_image_url="https://st-killian-resources.s3.amazonaws.com/kilian-celtic-logo-card_720x480.jpg",
            large_image_url="https://st-killian-resources.s3.amazonaws.com/kilian-celtic-logo-card_720x480.jpg"
        )

        return speech, reprompt, title, text, cardImage

    def resolveMassDay(self, massDay):
        """Resolve user speech into a desired mass day"""
        # First check for a holy day:
        holyDays = HolyDays()
        if holyDays.isHolyDay(massDay):
            LOGGER.info("Holy day detected: {}".format(massDay))
            targetDay = holyDays.getHolyDayEnumByName(massDay)
            targetDayName = holyDays.getHolyDayNameByEnum(targetDay)
            return targetDay, targetDayName

        # Next, assume it's a day of the week, homogenize:
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
            try:
                targetDay = list(calendar.day_name).index(massDay.title())
            except ValueError:
                return None, None
        return targetDay, targetDayName


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
