###############################################################################
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Kilian Parish, Mission Viejo, CA.
###############################################################################
"""Application for Amazon Alexa devices: "Saint Kilian".

Sample phrases:
 * Alexa, open Saint Kilian
 * When is the next mass
 * When is mass on Sunday
 * When is confession
 * What is on the calendar
 * Play the latest homily
 * Remind me to go to mass
 * What is the parish phone number

"""

# =============================================================================
# Imports
# =============================================================================
# Standard imports
import datetime
import logging
import random

# External imports
import pytz

# ASK imports
# - standard/core
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
    AbstractRequestInterceptor,
    AbstractResponseInterceptor
)
from ask_sdk_core.utils import is_request_type, is_intent_name

# - model
from ask_sdk_model import (
    DialogState,
    Intent,
    IntentConfirmationStatus,
    IntentRequest,
    Response,
    SlotConfirmationStatus,
    Slot
)
from ask_sdk_model.interfaces.audioplayer import (
    AudioItem,
    AudioItemMetadata,
    PlaybackNearlyFinishedRequest,
    PlayBehavior,
    PlayDirective,
    Stream,
    StopDirective,
)
from ask_sdk_model.interfaces.audioplayer.audio_player_state import (
    AudioPlayerState
)
from ask_sdk_model.dialog import DelegateDirective, ElicitSlotDirective
from ask_sdk_model.services import ServiceException
from ask_sdk_model.services.reminder_management import (
    AlertInfo,
    PushNotification,
    PushNotificationStatus,
    ReminderRequest,
    SpokenInfo,
    SpokenText,
    Trigger,
    TriggerType,
)
from ask_sdk_model.slu.entityresolution import StatusCode
from ask_sdk_model.ui import (
    AskForPermissionsConsentCard,
    SimpleCard,
    StandardCard
)
## Not sure why this import is different from line 34;
## commenting to see what happens:
#from ask_sdk_core.dispatch_components.exception_components import(
#    AbstractExceptionHandler
#)

# Local imports
import audio
import display
import events
import kilian_data
import session

sb = StandardSkillBuilder()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# =============================================================================
# Main Handler
# =============================================================================
class LaunchRequestHandler(AbstractRequestHandler):
    """Object handling all initial requests. Launches the skill."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        """Handle the launch request; fetch and serve appropriate response.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Raises:
            ValueError: If something other than the sanctioned app calls this
                intent.

        Returns:
            ask_sdk_model.response.Response: Response for this request and
                device.

        """
        # Prevent someone bad from writing a skill that sends requests to this:
        env = handler_input.request_envelope
        appId = env.session.application.application_id
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
class CalendarEventHandler(AbstractRequestHandler):
    """Object handling CalendarEventIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "What is on the calendar", "What events are coming up"

        """
        return is_intent_name("CalendarEventIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        userSession = session.KilianUserSession(handler_input)

        implemented = False
        if implemented:
            speech, reprompt, cardTitle, cardText, cardImage = \
                events.Calendar(userSession).getNextEvents()
            handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
            ).set_should_end_session(True)
            return handler_input.response_builder.response

        calendar = events.Calendar(userSession)
        speech, title, text, directive, sessionAttrs = \
            calendar.getNotImplementedResponse()

        card = StandardCard(title=title, text=text)
        handler_input.response_builder.speak(speech)
        handler_input.response_builder.set_card(card)
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)
        handler_input.attributes_manager.session_attributes = sessionAttrs
        return handler_input.response_builder.response


class ConfessionHandler(AbstractRequestHandler):
    """Object handling ConfessionIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "When is confession", "When is reconciliation"

        """
        return is_intent_name("ConfessionIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Ends the current session.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        speech, reprompt, cardTitle, cardText, cardImage, displayText = \
            events.Confession().getNextConfession()
        handler_input.response_builder.speak(speech).ask(reprompt)

        # Card for app:
        handler_input.response_builder.set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        )
        handler_input.response_builder.set_should_end_session(True)

        # Display directive for display devices (Echo Show, etc):
        directiveBuilder = display.Directive(
            mainUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/rosary_340.jpg",  # pylint: disable=C0301
            backgroundUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/dispBG_512.jpg",  # pylint: disable=C0301
            title=cardTitle,
            text=displayText
        )
        displayDirective = directiveBuilder.getDirective()

        # Check for displayDirective support:
        envelope = handler_input.request_envelope
        supported = envelope.context.system.device.supported_interfaces.to_dict()
        if supported.get('display'):
            LOGGER.info("display interface supported, adding display directive.")
            handler_input.response_builder.add_directive(displayDirective)
        else:
            LOGGER.info("display interface not supported, withholding directive.")

        return handler_input.response_builder.response

class LatestHomilyHandler(AbstractRequestHandler):
    """Object responding to initial requests.

    Triggers playback of the latest homily. Initializes AudioPlayer, ends the
    session.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "Play the latest homily", "Play Sunday's homily"

        """
        return is_intent_name("LatestHomilyIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Ends the current session with an audio directive.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        userSession = session.KilianUserSession(handler_input)
        homily = audio.Homily(userSession)
        speech, title, text, directive, sessionAttrs = \
            homily.getLatestHomily()

        card = StandardCard(title=title, text=text)
        handler_input.response_builder.speak(speech)
        handler_input.response_builder.set_card(card)
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)
        handler_input.attributes_manager.session_attributes = sessionAttrs
        return handler_input.response_builder.response


class LatestTalkHandler(AbstractRequestHandler):
    """Object responding to initial requests.

    Triggers playback of the latest talk. Initializes AudioPlayer, ends the
    session.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "Play the latest talk", "Play the newest talk"

        """
        return is_intent_name("LatestTalkIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Ends the current session with an audio directive.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        userSession = session.KilianUserSession(handler_input)
        talk = audio.Talk(userSession)
        speech, title, text, directive, sessionAttrs = \
            talk.getLatestTalk()

        card = StandardCard(title=title, text=text)
        handler_input.response_builder.speak(speech)
        handler_input.response_builder.set_card(card)
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)
        handler_input.attributes_manager.session_attributes = sessionAttrs
        return handler_input.response_builder.response


class MassTimeHandler(AbstractRequestHandler):
    """Object handling all initial requests. Handles MassTimeIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "What time is church", "When is mass on Wednesday"

        """
        return is_intent_name("MassTimeIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Ends the current session.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        LOGGER.info("__In MassTimeHandler__")
        userSession = session.KilianUserSession(handler_input)

        mass = events.MassResponse(userSession)
        speech, reprompt, cardTitle, cardText, cardImage, displayText = \
            mass.getMassTimeResponse()
        handler_input.response_builder.speak(speech).ask(reprompt)

        # Card for app:
        handler_input.response_builder.set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        )
        handler_input.response_builder.set_should_end_session(True)

        # Display Directive for display devices (Echo Show, etc):
        directiveBuilder = display.Directive(
            mainUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/massGifts_340.jpg",  # pylint: disable=C0301
            backgroundUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/dispBG_512.jpg",  # pylint: disable=C0301
            title=cardTitle,
            text=displayText
        )
        displayDirective = directiveBuilder.getDirective()

        # Check for displayDirective support:
        envelope = handler_input.request_envelope
        supported = envelope.context.system.device.supported_interfaces.to_dict()
        if supported.get('display'):
            LOGGER.info("display interface supported, adding display directive.")
            handler_input.response_builder.add_directive(displayDirective)
        else:
            LOGGER.info("display interface not supported, withholding directive.")

        return handler_input.response_builder.response


class NextMassHandler(AbstractRequestHandler):
    """Object handling all initial requests. Handles NextMassIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "What time is the next mass", "When is mass today"

        """
        env = handler_input.request_envelope
        return (is_intent_name("NextMassIntent")(handler_input)
                and env.request.dialog_state == DialogState.STARTED)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        If a mass is taking place today, does not end the current session.
        issues a ElicitSlotDirective to continue the dialog, asking the user
        if they would like a reminder.

        If no mass, then ends the current session.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        LOGGER.info("In NextMassHandler")
        userSession = session.KilianUserSession(handler_input)
        # Get response:
        envelope = handler_input.request_envelope
        speech, reprompt, cardTitle, cardText, cardImage, displayText = \
            events.MassResponse(userSession).getNextMassResponse()

        # If mass, prompt for a reminder; if not, return response.
        nextMass = events.MassResponse(userSession).getNextMass()
        if nextMass:
            msg = "Found a 'next mass' for today, constructing reminder request"
            LOGGER.debug(msg)
            speech += (". Would you like me to remind you "
                       "30 minutes prior to mass?")
            handler_input.response_builder.speak(speech).ask(reprompt).set_card(
                StandardCard(title=cardTitle, text=cardText, image=cardImage)
            ).set_should_end_session(False)
            #currentIntent = envelope.request.intent
            msg = "Reprompt message constructed. Now constructing nextIntent"
            LOGGER.debug(msg)
            nextIntent = Intent(
                name="NotifyNextMassIntent",
                confirmation_status=IntentConfirmationStatus.NONE,
                slots={
                    "DESIRES_REMINDER": Slot(
                        name="DESIRES_REMINDER",
                        confirmation_status=SlotConfirmationStatus.NONE
                    )
                }
            )
            #handler_input.response_builder.add_directive(
            #    DelegateDirective(updated_intent=nextIntent)
            #)
            msg = "nextMass constructed, now adding ElicitSlotDirective"
            LOGGER.debug(msg)
            handler_input.response_builder.add_directive(
                ElicitSlotDirective(
                    slot_to_elicit="DESIRES_REMINDER",
                    updated_intent=nextIntent
                )
            )
            msg = "Asking user if they want a reminder, and queuing follow-up intent."
            LOGGER.info(msg)
            msg = "Response looks like: \n{}".format(handler_input.response_builder.response)
            LOGGER.debug(msg)
            return handler_input.response_builder.response

        LOGGER.debug("No 'next mass' found for today. No reminder.")
        # No next mass, so ... no reminder needed:
        handler_input.response_builder.speak(speech).set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        )
        # Display Directive for display devices (Echo Show, etc):
        directiveBuilder = display.Directive(
            mainUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/massGifts_340.jpg",  # pylint: disable=C0301
            backgroundUrl="https://st-killian-resources.s3.amazonaws.com/displayTemplateMedia/dispBG_512.jpg",  # pylint: disable=C0301
            title=cardTitle,
            text=displayText
        )
        displayDirective = directiveBuilder.getDirective()

        # Check for displayDirective support:
        envelope = handler_input.request_envelope
        supported = envelope.context.system.device.supported_interfaces.to_dict()
        if supported.get('display'):
            LOGGER.info("display interface supported, adding display directive.")
            handler_input.response_builder.add_directive(displayDirective)
        else:
            LOGGER.info("display interface not supported, withholding directive.")

        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


class NotifyNextMassHandler(AbstractRequestHandler):
    """Object handling all initial requests. Handles NotifyNextMassIntent.

    Also responds as an updated_intent to a reminder prompt from NextMassIntent.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "Remind me to go to mass"

        """
        return is_intent_name("NotifyNextMassIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Handles prompt response if one exists (ie. if this was called as an
        updated_intent from NextMassIntent). Unless told not to, creates
        a reminder via the reminder API for 30 minutes prior to mass, handling
        edge cases such as being within a 30 minute window of next mass OR
        lack of Reminder permissions by the user.

        Supports a DEV_MODE for a quick reminder.

        Ends the current session.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        DEV_MODE = False
        speech = ""
        LOGGER.info("Running NotifyNextMassHandler")
        userSession = session.KilianUserSession(handler_input)

        negativeResponses = ["nah", "nope", "no thank you", "no thanks", "no"]

        # Did this intent come from an updated_intent redirect? Was the user
        #  just asked a yes/no question?:
        if userSession.desiresReminder:
            # Yup, check for a negative answer and bail.
            if userSession.desiresReminder.lower() in negativeResponses:
                LOGGER.info("DESIRES_REMINDER slot indicates 'no'")
                speech = "Okay."
                cardTitle = "Next Mass"
                cardText = "No reminder requested."
                handler_input.response_builder.speak(speech).set_card(
                    StandardCard(title=cardTitle, text=cardText)
                )
                handler_input.response_builder.set_should_end_session(True)
                return handler_input.response_builder.response
        else:
            # Nope, the user must have explicitly asked for the reminder.
            LOGGER.info("No DESIRES_REMINDER slot filled.")

        # Set up the reminder framework:
        responseBuilder = handler_input.response_builder
        requestEnvelope = handler_input.request_envelope
        permissions = requestEnvelope.context.system.user.permissions
        serviceFactory = handler_input.service_client_factory
        reminderService = serviceFactory.get_reminder_management_service()

        # If no permissions
        if not (permissions and permissions.consent_token):
            LOGGER.info("user hasn't granted reminder permission")
            speech = "Please give Saint Kilian permissions to set reminders"
            speech += " using your Alexa app."
            permissions = ["alexa::alerts:reminders:skill:readwrite"]
            card = AskForPermissionsConsentCard(permissions=permissions)
            return responseBuilder.speak(speech).set_card(card).response

        # Else, let's set up the reminder
        msg = "Necessary permissions found. Creating reminder."
        print(msg)
        LOGGER.info(msg)
        now = datetime.datetime.now(pytz.timezone("America/Los_Angeles"))
        massTime = events.MassResponse(userSession).getNextMass()
        msg = "massTime getNextMass query returned"
        print(msg)
        LOGGER.debug(msg)
        # If no more masses today:
        if not massTime:
            LOGGER.info("no next mass found for today")
            speech = "Sorry, but it looks like there are no more masses today."
            cardText = "No more masses today.\nTry again tomorrow."
            card = SimpleCard("St. Kilian - Mass Reminder", cardText)
            return responseBuilder.speak(speech).set_card(card) \
                .set_should_end_session(True).response

        # Good, a mass was found. Convert it to the local timezone.
        msg = "Mass found. Converting to local timezone"
        print(msg)
        LOGGER.debug(msg)
        massTime = massTime["time"]
        todayEvent = datetime.datetime.combine(now, massTime)
        reminderTime = todayEvent - datetime.timedelta(minutes=30)
        timezone = pytz.timezone("America/Los_Angeles")
        reminderTime = timezone.localize(reminderTime)
        todayEvent = timezone.localize(todayEvent)
        msg = "Upcoming event, local time, is {}".format(todayEvent)
        print(msg)
        LOGGER.debug(msg)
        # Are we within 30 minutes before it starts? If so, apologize and bail.
        if reminderTime < now and not DEV_MODE:
            LOGGER.info("too late. reminder is in the past.")
            speech = "It looks like it's too late for a reminder. "
            left = int(((todayEvent - now).seconds) / 60)
            speech += "You only have {} minutes left until Mass.".format(left)
            card = SimpleCard(
                "St. Kilian - Mass Reminder",
                "Reminder set for Mass."
            )
            return responseBuilder.speak(speech).set_card(card) \
                .set_should_end_session(True).response

        # Rather than waiting all day, if in dev mode, just wait one minute:
        if DEV_MODE:
            reminderTime = now + datetime.timedelta(minutes=+1)

        # Build and invoke the response:
        msg = "Building response"
        print(msg)
        LOGGER.debug(msg)
        reminderString = reminderTime.strftime("%Y-%m-%dT%H:%M:%S")
        trigger = Trigger(TriggerType.SCHEDULED_ABSOLUTE, reminderString,
                          time_zone_id="America/Los_Angeles")
        msg = "It is time to leave for mass."
        markup = "<speak>{}</speak>".format(msg)
        reminderSpeech = SpokenText(locale="en-US", ssml=markup, text=msg)
        alertInfo = AlertInfo(SpokenInfo(content=[reminderSpeech]))
        pushNotification = PushNotification(PushNotificationStatus.ENABLED)
        reminderRequest = ReminderRequest(
            request_time=reminderTime,
            trigger=trigger,
            alert_info=alertInfo,
            push_notification=pushNotification
        )
        try:
            LOGGER.debug("creating reminder...")
            print("creating reminder...")
            reminderService.create_reminder(reminder_request=reminderRequest)
            LOGGER.debug("reminder created.")
        except ServiceException as e:
            msg = "An error occurred while creating reminder from\n{}"
            msg = msg.format(reminderRequest)
            print(msg)
            LOGGER.error(msg)
            LOGGER.error(e)
            if hasattr(e, "message"):
                LOGGER.error(e.message)
            raise e

        # Build the speech response:
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
        card = SimpleCard("St. Kilian", "Reminder set for Mass.")
        msg = "returning final response."
        print(msg)
        return responseBuilder.speak(speech).set_card(card) \
            .set_should_end_session(True).response


class ParishPhoneHandler(AbstractRequestHandler):
    """Object handling all initial requests. Handles ParishPhoneIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample phrases: "What is the parish phone number"

        """
        return is_intent_name("ParishPhoneIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the intent; fetch and serve appropriate response.

        Ends the current session.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        Returns:
            ask_sdk_model.response.Response: Response for this intent and
                device.

        """
        speech, reprompt, cardTitle, cardText, cardImage = \
            getParishPhoneResponse()
        handler_input.response_builder.speak(speech).ask(reprompt).set_card(
            StandardCard(title=cardTitle, text=cardText, image=cardImage)
        ).set_should_end_session(True)
        return handler_input.response_builder.response


# =============================================================================
# Standard Handlers
# =============================================================================
class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Object handling all initial requests.

    Handles Amazon's built in Cancel, Stop, and Pause intents.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return not (not is_intent_name("AMAZON.CancelIntent")(handler_input)
                    and not is_intent_name("AMAZON.StopIntent")(handler_input)
                    and not is_intent_name("AMAZON.PauseIntent")(handler_input))

    def handle(self, handler_input):
        """Handle the request; fetch and serve appropriate response.

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


class ExceptionHandler(AbstractExceptionHandler):
    """Handler for fatal errors.

    If an exception is raised in the code, this response takes over.

    """
    def can_handle(self, handler_input, exception):
        """Handle everything."""
        return True

    def handle(self, handler_input, exception):
        """Handle the request; fetch and serve appropriate response.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        LOGGER.info("In ExceptionHandler")
        LOGGER.error("EXCEPTION!: {}".format(exception))
        speech = "Sorry, I've encountered an error in my code. "
        speech += "If this problem persists, "
        speech += "please inform the Saint Kilian parish office."
        reprompt = "I didn't catch that. What can I help you with?"
        return handler_input.response_builder.speak(speech).ask(
            reprompt).set_should_end_session(True).response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for fallback intent.

    If no appropriate intent or request handler can be found, this is
    called in its stead.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the request; fetch and serve appropriate response.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        LOGGER.info("In FallbackIntentHandler")
        speech = "Sorry, I'm not sure how to help you with that. "
        speech += "You can try asking when is the next Mass."
        reprompt = "I didn't catch that. What can I help you with?"
        return handler_input.response_builder.speak(speech).ask(
            reprompt).response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for help intent.

    When the user asks for help, this is the response.

    """
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled."""
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the request; fetch and serve appropriate response.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        LOGGER.info("In HelpIntentHandler")
        speech = "Saint Kilian can help you with the following requests. "
        speech += "What time is mass? When is mass on Sunday? "
        speech += "When is the next mass? Remind me to go to mass. "
        speech += "When is confession? "
        speech += "What is the parish office phone number? "
        speech += "Now, how may I help you?"
        reprompt = "I didn't catch that. What can I help you with?"
        handler_input.response_builder.set_should_end_session(False)
        return handler_input.response_builder.speak(speech).ask(
            reprompt).response


# =============================================================================
# Audio Handlers
# =============================================================================
class AudioNextIntentHandler(AbstractRequestHandler):
    """Handles AudioPlayer request NextIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        Sample Phrases: "Next", "Skip"

        """
        return is_intent_name("AMAZON.NextIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        Since this skill doesn't support a stream of audio files, this simply
        returns a no-op response.

        Ends session as is required by the AudioPlayer.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


class AudioPlaybackFinishedHandler(AbstractRequestHandler):
    """Handles AudioPlayer request PlaybackFinished."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when playback finishes.

        """
        return is_request_type("AudioPlayer.PlaybackFinished")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        Since we needn't take any action, this returns a no-op.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        return {}


class AudioPlaybackNearlyFinishedHandler(AbstractRequestHandler):
    """Handles AudioPlayer request PlaybackNearlyFinished."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when playback of one track
        begins to near completion, and it is time to queue the next track.

        """
        myType = "AudioPlayer.PlaybackNearlyFinished"
        return is_request_type(myType)(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        Since we needn't queue any more tracks, this returns a no-op.

        Ends session as is required by the AudioPlayer.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


class AudioPlaybackStartedHandler(AbstractRequestHandler):
    """Handles AudioPlayer request PlaybackStarted."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when playback of one track
        begins.

        """
        return is_request_type("AudioPlayer.PlaybackStarted")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        Since we needn't do anything, this returns a no-op.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        return {}


class AudioPlaybackStoppedHandler(AbstractRequestHandler):
    """Handles AudioPlayer request PlaybackStopped."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when playback of one track
        stops.

        """
        return is_request_type("AudioPlayer.PlaybackStopped")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        This gives us the opportunity when playback stops to record the
        current playback time as an offset in milliseconds that can then
        be reapplied if the track is ever resumed.

        This returns a no-op.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        msg = "Audio playback stopped."
        LOGGER.info(msg)

        oim = handler_input.request_envelope.request.offset_in_milliseconds
        userSession = session.KilianUserSession(handler_input)
        userSession.offsetInMilliseconds = oim
        userSession.savePersistentAttrs()

        msg = "Stored offsetInMilliseconds: {}".format(oim)
        LOGGER.info(msg)

        return {}


class AudioPreviousIntentHandler(AbstractRequestHandler):
    """Handles AudioPlayer intent PreviousIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when a user asks for
        the previous track.

        """
        return is_intent_name("AudioPlayer.PreviousIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        Since we don't support a playlist, this returns a no-op.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        return {}


class AudioResumeIntentHandler(AbstractRequestHandler):
    """Handles AudioPlayer intent ResumeIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when a user asks a track
        to resume.

        """
        return (is_intent_name("AudioPlayer.ResumeIntent")(handler_input) or
                is_intent_name("AMAZON.ResumeIntent")(handler_input)
               )

    def handle(self, handler_input):
        """Handle the request.

        We need to look up the last track that was playing, along with its
        playback time from which we need to resume, expressed in milliseconds
        offset from zero.  We then need to build and send the playback directive
        which will contain that information.

        Ends session as is required by the AudioPlayer.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        msg = "Resuming audio playback..."
        LOGGER.info(msg)

        userSession = session.KilianUserSession(handler_input)
        track = userSession.lastTrack
        token = userSession.lastToken
        offsetInMilliseconds = userSession.offsetInMilliseconds

        title = "Latest Homily"
        text = title

        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    expected_previous_token=None,
                    token=token,
                    url=track,
                    offset_in_milliseconds=offsetInMilliseconds
                ),
                metadata=AudioItemMetadata(
                    title="Latest Homily",
                    subtitle=text,
                )
            )
        )
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


class AudioStartOverIntentHandler(AbstractRequestHandler):
    """Handles AudioPlayer intent StartOverIntent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when a user asks for
        a track to start over.

        """
        return is_intent_name("AMAZON.StartOverIntent")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        We need to know the track that was playing last. We can give it
        an offset of zero, ensuring that it plays from the beginning as
        requested. We then need to build and deliver the directive.

        Ends session as is required by the AudioPlayer.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        userId = handler_input.request_envelope.context.system.user.user_id
        dataMan = kilian_data.KilianDataManager()
        dbEntry = dataMan.getUserDatabaseEntry(userId)
        track = dbEntry.get("lastTrack")
        token = dbEntry.get("lastToken")
        if not track:
            LOGGER.info("No lastTrack found in database! Can't start over.")
            return {}
        LOGGER.info("Starting over, track: {}".format(track))

        offsetInMilliseconds = 0

        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    expected_previous_token=None,
                    token=token,
                    url=track,
                    offset_in_milliseconds=offsetInMilliseconds
                ),
                metadata=AudioItemMetadata(
                    title="Latest Homily",
                    subtitle="Latest Homily",
                )
            )
        )
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


class AudioStopIntentHandler(AbstractRequestHandler):
    """Handles AudioPlayer request Cancel, Stop, and Pause Intent."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        This request is sent by the AudioPlayer when a user asks for
        a track to stop playing or to pause playback.

        """
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input) or
                is_intent_name("AMAZON.PauseIntent")(handler_input)
               )

    def handle(self, handler_input):
        """Handle the request.

        In case we need to resume this playback later, we need to store
        the track being played along with its offset in time, expressed as
        milliseconds offset from zero. We then need to build and deliver
        the stop directive.

        Ends session as is required by the AudioPlayer.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        msg = "Cancel, Stop, or Pause intent received."
        LOGGER.info(msg)

        env = handler_input.request_envelope
        audioPlayer = env.context.audio_player
        if audioPlayer.to_dict().get("player_activity") == "STOPPED":
            LOGGER.info("Audio player has been stopped.")
            oim = audioPlayer.to_dict().get("offset_in_milliseconds", 0)
            userSession = session.KilianUserSession(handler_input)
            userSession.offsetInMilliseconds = oim
            LOGGER.info("Saving offset of {} milliseconds".format(oim))
            userSession.savePersistentAttrs()

        directive = StopDirective()
        handler_input.response_builder.add_directive(directive)
        handler_input.response_builder.set_should_end_session(True)

        return handler_input.response_builder.response


class AudioUnsupportedHandler(AbstractRequestHandler):
    """Handles all unsupported AudioPlayer intents with a no-op response."""
    def can_handle(self, handler_input):
        """Inform the request handler of what intents can be handled.

        These requests are sent by the AudioPlayer when a user asks
        for various actions to take place in regards to the current track.

        """
        return (is_intent_name("AMAZON.LoopOffIntent")(handler_input) or
                is_intent_name("AMAZON.LoopOnIntent")(handler_input) or
                is_intent_name("AMAZON.RepeatIntent")(handler_input) or
                is_intent_name("AMAZON.ShuffleOffIntent")(handler_input) or
                is_intent_name("AMAZON.ShuffleOnIntent")(handler_input)
               )

    def handle(self, handler_input):
        """Handle the request.

        Since these are unsupported actions, this returns a no-op.

        Args:
            handler_input (ask_sdk_core.handler_input.HandlerInput):
                Input from Alexa.

        """
        return {}


# =============================================================================
# Request and Response Loggers
# =============================================================================
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        """Log the request, run when a request comes in."""
        LOGGER.info("Request Envelope: {}".format(
            handler_input.request_envelope
        ))

class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        """Log the response, run when a response goes out."""
        LOGGER.info("Response: {}".format(response))


# =============================================================================
# Session Ended Handler
# =============================================================================
class SessionEndedRequestHandler(AbstractRequestHandler):
    """When the skill ends, or a user exits a session."""
    def can_handle(self, handler_input):
        """Inform the system of requests that can be handled."""
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        """Handle the request.

        End the session with a cute message.
        Since we currently don't have an intent that maintains the session,
        this will likely never get called.

        """
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
    """Generate spoken response to phone number query"""
    speech = "The phone number for the Saint Kilian Parish Office is, "

    dataManager = kilian_data.KilianDataManager()
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
    """Generate generic welcome response upon initial startup."""
    #speech = "Welcome to Saint Kilian Parish, Mission Viejo. "
    speech = "<speak>"
    speech += '<audio src="https://st-killian-resources.s3.amazonaws.com/killianWelcome01_ssml.mp3"></audio> '  # pylint: disable=C0301
    speech += "How may I be of service?"
    speech += "</speak>"
    reprompt = "Try asking: when is the next Mass."
    title = "St. Kilian Parish, Mission Viejo"
    text = "Try asking 'When is the next mass?'"
    cardImage = None
    return speech, reprompt, title, text, cardImage

# =============================================================================
# Skill Builder
# =============================================================================
sb.add_request_handler(AudioNextIntentHandler())
sb.add_request_handler(AudioPlaybackFinishedHandler())
sb.add_request_handler(AudioPlaybackNearlyFinishedHandler())
sb.add_request_handler(AudioPlaybackStartedHandler())
sb.add_request_handler(AudioPlaybackStoppedHandler())
sb.add_request_handler(AudioPreviousIntentHandler())
sb.add_request_handler(AudioResumeIntentHandler())
sb.add_request_handler(AudioStartOverIntentHandler())
sb.add_request_handler(AudioStopIntentHandler())
sb.add_request_handler(AudioUnsupportedHandler())

sb.add_request_handler(CalendarEventHandler())
sb.add_request_handler(ConfessionHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(LatestHomilyHandler())
sb.add_request_handler(LatestTalkHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MassTimeHandler())
sb.add_request_handler(NextMassHandler())
sb.add_request_handler(NotifyNextMassHandler())
sb.add_request_handler(ParishPhoneHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(ExceptionHandler())

sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())
handler = sb.lambda_handler()  # pylint: disable=C0103
