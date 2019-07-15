class KillianUserSession(object):
    def __init__(self, handler_input):
        self._handler_input = handler_input
        self.slots = {}

        self._sessionAttributes = self.populateAttrs()

    @property
    def massDay(self):
        return self.slots.get("massDay", {}).get("value")

    def populateAttrs(self):
        print("populating attrs")
        self._sessionAttributes = \
            self._handler_input.attributes_manager.request_attributes
        self._sessionAttributes["userId"] = \
            self._handler_input.request_envelope.context.system.user.user_id

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

