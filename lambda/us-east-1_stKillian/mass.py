import calendar
import datetime
import logging
import pytz

import killian_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Mass(object):
    def __init__(self, userSession):
        self.userSession = userSession

    def getMassTimeResponse(self, massDay=None):
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
                if targetDay > 6:
                    targetDay = 0
                targetDayName = "Tomorrow, {}".format(calendar.day_name[targetDay])
            else:
                targetDayName = massDay
                targetDay = list(calendar.day_name).index(massDay.title())
        else:
            todayUtc = datetime.datetime.now(tz=pytz.utc)
            timezone = pytz.timezone("America/Los_Angeles")
            todayLocal = todayUtc.astimezone(timezone)
            targetDay = todayLocal.weekday()
            targetDayName = "Today"

        times = dataManager.getMassTimes(targetDay)

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


    def getNextMassResponse(self):
        speech = ""
        dataManager = killian_data.KillianDataManager()
        today = datetime.datetime.now(tz=pytz.utc)
        logger.info("-- today (utc?): {}".format(today))
        timezone = pytz.timezone("America/Los_Angeles")
        todayLocal = today.astimezone(timezone)
        logger.info("-- today (local): {}".format(todayLocal))
        todayNum = todayLocal.weekday()
        times = dataManager.getMassTimes(todayNum)
        # TODO: If not times...
        lastMassTime = times[-1][0]
        nowTime = todayLocal.time()
        logger.info("Mass today?({}), at {}".format(todayNum, nowTime))
        if nowTime > lastMassTime:
            logger.info("No more masses today({}), at {}".format(todayNum, nowTime))
            speech += "There are no more masses today. "
            tSpeech, reprompt, _, _, _ = self.getMassTimeResponse(
                massDay="tomorrow"
            )
            speech += tSpeech
        else:
            i = 0
            bestMass = times[i][0]
            while nowTime < bestMass:
                i += 1
                bestMass = times[i][0]
            massString = convertMassToString(bestMass, language=times[i][1])
            speech = "The next mass today will be at {}".format(massString)
        title = "Next Mass"
        text = speech
        cardImage = None
        return speech, reprompt, title, text, cardImage

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
