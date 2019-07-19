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
from ask_sdk_model import (DialogState, Intent, IntentConfirmationStatus, 
    IntentRequest, Response, SlotConfirmationStatus, Slot)
from ask_sdk_model.dialog import DelegateDirective, ElicitSlotDirective
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import (
    Trigger, TriggerType, AlertInfo, SpokenInfo, SpokenText, PushNotification,
    PushNotificationStatus, ReminderRequest)
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_model.ui import (
    AskForPermissionsConsentCard, SimpleCard, StandardCard)

# Local imports
import killian_data
import events
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
            events.Mass(userSession).getMassTimeResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(False)
        return handler_input.response_builder.response


class NextMassHandler(AbstractRequestHandler):
    """Object handling all initial requests."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return (is_intent_name("NextMassIntent")(handler_input)
                and handler_input.request_envelope.request.dialog_state == DialogState.STARTED)
                #and not handler_input.request_envelope.request.dialog_state == DialogState.COMPLETED)

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

        envelope = handler_input.request_envelope
        speech, reprompt, cardTitle, cardText, cardImage = \
            events.Mass(userSession).getNextMassResponse()

        nextMass = events.Mass(userSession).getNextMass()
        if nextMass:
            speech += ". Would you like me to remind you 30 minutes prior to mass?"
            handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
            ).set_should_end_session(False)
            #currentIntent = envelope.request.intent
            nextIntent = Intent(
                name="NotifyNextMassIntent",
                confirmation_status=IntentConfirmationStatus.NONE,
                slots = {
                    "DESIRES_REMINDER": Slot(
                        name="DESIRES_REMINDER",
                        confirmation_status=SlotConfirmationStatus.NONE
                    )
                }
            )
            #handler_input.response_builder.add_directive(
            #    DelegateDirective(updated_intent=nextIntent)
            #)
            handler_input.response_builder.add_directive(
                ElicitSlotDirective(
                    slot_to_elicit = "DESIRES_REMINDER",
                    updated_intent = nextIntent
                )
            )
            return handler_input.response_builder.response

        # No next mass, so ... no reminder needed:
        handler_input.response_builder.speak(speech).set_card(
            StandardCard(title=cardTitle, text=cardText)
        )
        handler_input.response_builder.should_end_session(True)
        return handler_input.response_builder.response


class NotifyNextMassHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NotifyNextMassIntent")(handler_input)

    def handle(self, handler_input):
        DEV_MODE = True
        speech = ""
        logging.info("Running NotifyNextMassHandler")
        userSession = session.KillianUserSession(handler_input)

        negativeResponses = ["nah", "nope", "no thank you", "no thanks", "no"]

        if userSession.desiresReminder:
            if userSession.desiresReminder.lower() in negativeResponses:
                logger.info("DESIRES_REMINDER slot indicates 'no'")
                speech = "Okay."
                cardTitle = "Next Mass"
                cardText = "No reminder requested."
                handler_input.response_builder.speak(speech).set_card(
                    StandardCard(title=cardTitle, text=cardText)
                )
                handler_input.response_builder.set_should_end_session(True)
                return handler_input.response_builder.response
        else:
            logger.info("No DESIRES_REMINDER slot filled.")

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
        massTime = events.Mass(userSession).getNextMass()
        if not massTime:
            logging.info("no next mass found for today")
            speech = "Sorry, but it looks like there are no more masses today."
            card = SimpleCard("St. Killian", "Reminder set for Mass.")
            return responseBuilder.speak(speech).set_card(card) \
                .set_should_end_session(True).response

        massTime = massTime["time"]
        todayEvent = datetime.datetime.combine(now, massTime)
        reminderTime = todayEvent - datetime.timedelta(minutes=30)
        timezone = pytz.timezone("America/Los_Angeles")
        reminderTime = timezone.localize(reminderTime)
        if reminderTime < now:
            logging.info("too late. reminder is in the past.")
            speech = "It looks like it's too late for a reminder. "
            left = int(((reminderTime - now).seconds) / 60)
            speech += "You only have {} minutes left until Mass.".format(left)
            card = SimpleCard("St. Killian", "Reminder set for Mass.")
            return responseBuilder.speak(speech).set_card(card) \
                .set_should_end_session(True).response

        if DEV_MODE:
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

        if DEV_MODE:
            speech += "Okay. Since you are in demo mode, I'll remind "
            speech += "in one minute to go to mass. "
        speech += "I will remind you at {}:{}{} to leave for mass."
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
# Standard Handlers
# =============================================================================
class CancelAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return not (not is_intent_name("AMAZON.CancelIntent")(handler_input)
                and not is_intent_name("AMAZON.StopIntent")(handler_input)
                and not is_intent_name("AMAZON.PauseIntent")(handler_input))

    def handle(self, handler_input):
        """Handle the launch request; fetch and serve appropriate response.
        
        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        speech = "Canceling"
        # See AudioPlayer code - will become relevant
        responseBuilder = handler_input.response_builder
        responseBuilder.speak(speech).ask(speech)
        #directive = audioplayer.StopDirective()
        #responseBuilder.add_directive(directive)
        responseBuilder.set_should_end_session(True)
        return handler_input.response_builder.response

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
    speech += "when is the next Mass."
    reprompt = "Try asking: when is the next Mass."
    title = "St. Killian Parish, Mission Viejo"
    text = "Try asking 'When is the next mass?'"
    cardImage = None
    return speech, reprompt, title, text, cardImage

# =============================================================================
# Skill Builder
# =============================================================================
sb.add_request_handler(CancelAndStopIntentHandler())
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



