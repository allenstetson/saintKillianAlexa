###############################################################################
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
###############################################################################
"""Application for Amazon Alexa devices: "Saint Killian". """

# =============================================================================
# Imports
# =============================================================================
# Standard imports
import datetime
import logging
import pytz
import random

# ASK imports
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import (AbstractExceptionHandler,
    AbstractRequestHandler, AbstractRequestInterceptor,
    AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import (Response, IntentRequest, DialogState,
    SlotConfirmationStatus, Slot)
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import (
    Trigger, TriggerType, AlertInfo, SpokenInfo, SpokenText, PushNotification,
    PushNotificationStatus, ReminderRequest)
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_model.ui import (
    AskForPermissionsConsentCard, SimpleCard, StandardCard)

# Local imports
import killian_data
import mass
import session

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
        userSession = session.KillianUserSession(handler_input)

        speech, reprompt, cardTitle, cardText, cardImage = \
            mass.Mass(userSession).getMassTimeResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response


class NextMassHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("NextMassIntent")(handler_input)

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
        userSession = session.KillianUserSession(handler_input)

        speech, reprompt, cardTitle, cardText, cardImage = \
            mass.Mass(userSession).getNextMassResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response

class NotifyNextMassHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NotifyNextMassIntent")(handler_input)

    def handle(self, handler_input):
        logging.info("Running NotifyNextMassHandler")
        responseBuilder = handler_input.response_builder
        requestEnvelope = handler_input.request_envelope
        permissions = requestEnvelope.context.system.user.permissions
        serviceFactory = handler_input.service_client_factory
        reminderService = serviceFactory.get_reminder_management_service()

        # If no permissions
        if not (permissions and permissions.consent_token):
            logging.info("user hasn't granted reminder permission")
            speech = "Please give Saint Killian permissions to set reminders"
            speech += " using your Alexa app."
            permissions = ["alexa::alerts:reminders:skill:readwrite"]
            card = AskForPermissionsConsentCard(permissions=permissions)
            return responseBuilder.speak(speech).set_card(card).response

        # Else, let's set up the permission
        logging.info("Necessary permissions found. Creating reminder.")
        now = datetime.datetime.now(pytz.timezone("America/Los_Angeles"))
        reminderTime = now + datetime.timedelta(minutes=+1)
        reminderString = reminderTime.strftime("%Y-%m-%dT%H:%M:%S")
        trigger = Trigger(TriggerType.SCHEDULED_ABSOLUTE, reminderString,
                          time_zone_id="America/Los_Angeles")
        msg = "It is time to leave for mass."
        markup = "<speak>{}</speak>".format(msg)
        reminderSpeech = SpokenText(locale="en-US", ssml=markup, text=msg)
        alertInfo = AlertInfo(SpokenInfo([reminderSpeech]))
        pushNotification = PushNotification(PushNotificationStatus.ENABLED)
        reminderRequest = ReminderRequest(reminderTime, trigger, alertInfo,
                                          pushNotification)
        try:
            response = reminderService.create_reminder(reminderRequest)
        except ServiceException as e:
            logger.error(e)
            raise e

        speech = "I will remind you at {}:{}{} to leave for mass."
        hour = reminderTime.hour
        minute = "{:02d}".format(reminderTime.minute)
        if hour >= 12:
            suffix = "pm"
        else:
            suffix = "am"

        if hour > 12:
            hour = hour - 12
        speech = speech.format(hour, minute, suffix)
        card = SimpleCard("St. Killian", "Reminder set for Mass.")
        return responseBuilder.speak(speech).set_card(card) \
            .set_should_end_session(True).response


class ParishPhoneHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("ParishPhoneIntent")(handler_input)

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
        speech, reprompt, cardTitle, cardText, cardImage = getParishPhoneResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response


# =============================================================================
# Fallback Handler
# =============================================================================
class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for fallback intent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

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
        logger.info("In FallbackIntentHandler")
        speech = "Sorry, I'm not sure how to help you with that. "
        speech += "You can try asking when is the next Mass."
        reprompt = "I didn't catch that. What can I help you with?"
        return handler_input.response_builder.speak(speech).ask(
                reprompt).response


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
# Session Ended Handler
# =============================================================================
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        speeches = [
            "Okay.",
            "Farewell.",
            "God bless."
        ]
        speech = random.choice(speeches)
        responseBuilder = handler_input.response_builder
        responseBuilder.speak(speech).ask(speech)
        responseBuilder.set_should_end_session(True)
        return responseBuilder.response


# =============================================================================
# Functions
# =============================================================================
def getParishPhoneResponse():
    speech = "The phone number for the Saint Killian Parish Office is, "

    dataManager = killian_data.KillianDataManager()
    number = dataManager.getParishOfficePhoneNumber()
    speech += ", ".join(number)
    reprompt = "Try asking: when is the next Mass."
    title = "Parish Office Phone Number"

    prettyNumber = "+1.{}.{}.{}".format(
        number[:3],
        number[3:6],
        number[6:]
    )
    text = prettyNumber
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
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MassTimeHandler())
sb.add_request_handler(NextMassHandler())
sb.add_request_handler(NotifyNextMassHandler())
sb.add_request_handler(ParishPhoneHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())
handler = sb.lambda_handler()



