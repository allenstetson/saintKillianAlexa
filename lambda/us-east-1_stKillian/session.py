# ==============================================================================
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
# ==============================================================================
"""Module containing helper object that tracks user session, id, attrs."""

__all__ = ["KillianUserSession"]

# ==============================================================================
# Imports
# ==============================================================================
# local imports
import killian_data

class KillianUserSession(object):
    """Object for tracking & accessing user data, session data, working with DB.
    
    Args:
        handler_input (ask_sdk_core.handler_input.HandlerInput):
            Input from Alexa.

    """
    def __init__(self, handler_input):
        self._dataMan = killian_data.KillianDataManager()
        self._dbEntry = {}
        self._handler_input = handler_input
        self._userId = None
        self.slots = {}

        self._sessionAttributes = self.populateAttrs()
        self.populateDbEntry()

    @property
    def dbEntry(self):
        """The database entry/record for this session in its entirety."""
        if self._dbEntry:
            return self._dbEntry
        self._dbEntry = self._dataMan.getUserDatabaseEntry(self.userId)
        return self._dbEntry

    @property
    def desiresReminder(self):
        """Slot indicating whether the user has asked for a reminder."""
        return self.slots.get("DESIRES_REMINDER", {}).get("value")

    @property
    def lastToken(self):
        """Persistent attr for tracking the last AudioPlayer token."""
        return self.dbEntry.get("lastToken", "")

    @lastToken.setter
    def lastToken(self, value):
        self._dbEntry["lastToken"] = value

    @property
    def lastTrack(self):
        """Persistent attr for tracking the last AudioPlayer track."""
        return self.dbEntry.get("lastTrack", "")

    @lastTrack.setter
    def lastTrack(self, value):
        self._dbEntry["lastTrack"] = value

    @property
    def massDay(self):
        """Slot for which day the user is interested in mass times."""
        return self.slots.get("massDay", {}).get("value")

    @property
    def offsetInMilliseconds(self):
        """Persistent attr for the last known AudioPlayer offset."""
        return self._dbEntry.get("offsetInMilliseconds", 0)

    @offsetInMilliseconds.setter
    def offsetInMilliseconds(self, value):
        self._dbEntry["offsetInMilliseconds"] = value

    @property
    def userId(self):
        """The current user's Amazon ID (pulled from session context)."""
        if self._userId:
            return self._userId
        env = self._handler_input.request_envelope
        self._userId = env.context.system.user.user_id
        return self._userId

    def populateAttrs(self):
        """Pulls data from the session and database to fill all session attrs.
        
        This includes Slots, Persistent Attributes, and User ID.
        
        """
        print("populating attrs")
        self._sessionAttributes = \
            self._handler_input.attributes_manager.request_attributes
        self._sessionAttributes["userId"] = \
            self._handler_input.request_envelope.context.system.user.user_id

        # If this is a request such as PlaybackStopped, it won't have an intent
        if not hasattr(self._handler_input.request_envelope.request, "intent"):
            return

        filledSlots = self._handler_input.request_envelope.request.intent.slots
        print("Filled slots: {} ({})".format(filledSlots, type(filledSlots)))
        if not filledSlots:
            return

        slots = {}
        for slotName in filledSlots:
            slots[slotName] = filledSlots[slotName].to_dict()
            try:
                slots[slotName]['status'] = str(
                    filledSlots[slotName].resolutions.resolutions_per_authority[0].status.code)
            except (TypeError, AttributeError) as e:
                slots[slotName]['status'] = None

            try:
                slots[slotName]['id'] = str(
                    filledSlots[slotName].resolutions.resolutions_per_authority[0].values[0].value.id)
            except (TypeError, AttributeError) as e:
                slots[slotName]['id'] = None
        print("Slots: {}".format(slots))
        self.slots = slots

    def populateDbEntry(self):
        """Fetches data from the user's database record into memory."""
        self._dbEntry = self._dataMan.getUserDatabaseEntry(self.userId)

    def savePersistentAttrs(self):
        """Writes data in memory to the user's database record."""
        self._dataMan.updateUserDatabaseEntry(self.userId, self.dbEntry)
