###############################################################################
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
###############################################################################
"""Application for Amazon Alexa devices: "Saint Killian". """

# =============================================================================
# Imports
# =============================================================================
# Standard imports
import calendar
import datetime
import logging

# ASK imports
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import (AbstractExceptionHandler,
        AbstractRequestHandler, AbstractRequestInterceptor,
        AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import (Response, IntentRequest, DialogState,
        SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_model.ui import SimpleCard, StandardCard


sb = StandardSkillBuilder()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# =============================================================================
# Main Handler
# =============================================================================
class LaunchRequestHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        """Handle the launch request; fetch and serve appropriate response.
        
        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Raises:
            ValueError:
                If something other than the sanctioned app calls this intent.

        Returns:
            ask_sdk_model.response.Response
                Response for this intent and device.
        
        """
        # Prevent someone bad from writing a skill that sends requests to this:
        appId = handler_input.request_envelope.session.application.application_id
        if appId != "amzn1.ask.skill.66eb11d8-013f-4fca-b655-494dbeba291b":
            raise ValueError("Invalid Application ID")

        speech, reprompt, cardTitle, cardText, cardImage = getWelcomeResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response

# =============================================================================
# Handlers
# =============================================================================
class MassTimeHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("MassTimeIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the launch request; fetch and serve appropriate response.
        
        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Raises:
            ValueError:
                If something other than the sanctioned app calls this intent.

        Returns:
            ask_sdk_model.response.Response
                Response for this intent and device.
        
        """
        speech, reprompt, cardTitle, cardText, cardImage = getMassTimeResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response

class NextMassHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("nextMassIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the launch request; fetch and serve appropriate response.
        
        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Raises:
            ValueError:
                If something other than the sanctioned app calls this intent.

        Returns:
            ask_sdk_model.response.Response
                Response for this intent and device.
        
        """
        speech, reprompt, cardTitle, cardText, cardImage = getNextMassResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response

# =============================================================================
# Request and Response Loggers
# =============================================================================
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        logger.info("Request Envelope: {}".format(
            handler_input.request_envelope
        ))

class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        logger.info("Response: {}".format(response))

# =============================================================================
# Functions
# =============================================================================
def getMassTimeResponse(massDay=None):
    filledSlots = handler_input.request_envelope.request.intent.slots
    massDayData = filledSlots["massDay"].to_dict()
    massDay = massDayData['value']

    isToday = False
    targetDay = None
    if massDay:
        today = datetime.date.today().weekday()
        todayName = calendar.day_name[today]
        if todayName == massDay:
            targetDay = today
            targetDayName = "Today"
        else:
            targetDayName = [x for x in calendar.day_name \
                    if x.lower() == massDay]
            targetDay = list(calendar.day_name).index(massDay.title())
    else:
        targetDay = datetime.date.today().weekday()
        targetDayName = "Today"

    # times = killian_events.Mass.getTimesForDay(targetDay)
    times = [
            datetime.time(7, 30),
            datetime.time(9, 0),
            datetime.time(10, 45),
            datetime.time(5, 0)
    ]

    timeStrings = set()
    for massTime in times:
        hour = massTime.hour
        if hour > 11:
            suffix = "pm"
        else:
            suffix = "am"
        if hour > 12:
            hour = hour - 12
        timeStrings.add("{}:{} {}".format(hour, massTime.minute, suffix))
    timeString = ", ".join(timeStrings)

    speech = "{}, the mass times are {}.".format(timeString)

    reprompt = "Try asking: when is the next Mass."
    title = "Mass Times: St. {}".format(targetDayName)
    text = "{} mass times:\n{}".format(targetDayName, timeString)
    cardImage = None
    return speech, reprompt, title, text, cardImage


def getNextMassResponse():
    speech = "The next mass today is at 5 o'clock p.m."
    reprompt = "Try asking: when is the next Mass."
    title = "Next Mass: St. Killian Parish"
    text = "Today's next Mass is at 5pm"
    cardImage = None
    return speech, reprompt, title, text, cardImage


def getWelcomeResponse():
    speech = "Welcome to Saint Killian Parish, Mission Viejo. You can ask "
    speech += "when is the next Mass. Other options are coming soon."
    reprompt = "Try asking: when is the next Mass."
    title = "St. Killian Parish, Mission Viejo"
    text = "Try asking 'When is the next mass?'"
    cardImage = None
    return speech, reprompt, title, text, cardImage

# =============================================================================
# Skill Builder
# =============================================================================
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NextMassHandler())

sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())
handler = sb.lambda_handler()



