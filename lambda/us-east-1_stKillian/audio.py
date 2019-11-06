###############################################################################
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Kilian Parish, Mission Viejo, CA.
###############################################################################
"""Module for serving audio directives for appropriate requests."""

# ASK imports
from ask_sdk_model.interfaces.audioplayer import (
    PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata,
    StopDirective, AudioPlayerState)

# Local imports
import kilian_data
import session


__all__ = ["Homily", "Talk"]


class Homily:
    """Object representing recorded homilies to be played by request."""
    def __init__(self, userSession):
        self.userSession = userSession

    def getLatestHomily(self):
        """Determine the latest recorded homily & return a directive for it."""
        #homilyUrl = "https://st-killian-resources.s3.amazonaws.com/homilies/06-17-19_TheChristianLifeIsLikeAJob.mp3"
        homilyUrl = "https://st-killian-resources.s3.amazonaws.com/homilies/killianGeneric_mixdown.mp3"
        #token = "06-17-19_TheChristianLifeIsLikeAJob"
        token = "kilianGeneric_mixdown"

        #speech = "Okay. Here is a homily from Sunday, "
        #speech += "June seventeenth by Father Dwyer. "
        #title = "Latest Homily"
        #text = "June 17, 2019 Father Dwyer"
        speech = ""
        title = "St. Kilian audio"
        text = "St. Kilian audio coming soon!"

        self.userSession.lastToken = token
        self.userSession.lastTrack = homilyUrl
        self.userSession.savePersistentAttrs()

        sessionAttrs = {
            "lastTrack": homilyUrl,
            "lastToken": token
        }

        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    expected_previous_token=None,
                    token=token,
                    url=homilyUrl,
                    offset_in_milliseconds=0
                ),
                metadata=AudioItemMetadata(
                    title="Latest Homily",
                    subtitle=text
                )
            )
        )
        return speech, title, text, directive, sessionAttrs


class Talk:
    """Object representing recorded talks to be played by request."""
    def __init__(self, userSession):
        self.userSession = userSession

    def getLatestTalk(self):
        """Determine the latest recorded talk & return a directive for it."""
        dataMan = kilian_data.KilianDataManager()
        talk = dataMan.getLatestTalk()
        talkUrl = talk['url']
        token = talk['namespace']

        talkDate = datetime.date(item["eventYear"], item["eventMonth"], item["eventDay"])
        speech = "Okay. Here is a talk from  "
        speech += "{}".format(talkDate.strftime("%A, %B %d, %Y"))
        title = "St. Kilian: Latest Talk"
        text = talk['eventTitle']

        self.userSession.lastToken = token
        self.userSession.lastTrack = talkUrl
        self.userSession.savePersistentAttrs()

        sessionAttrs = {
            "lastTrack": talkUrl,
            "lastToken": token
        }

        directive = PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    expected_previous_token=None,
                    token=token,
                    url=talkUrl,
                    offset_in_milliseconds=0
                ),
                metadata=AudioItemMetadata(
                    title="Latest Talk",
                    subtitle=text
                )
            )
        )
        return speech, title, text, directive, sessionAttrs
