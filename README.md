# saintKillianAlexa
Alexa skill for St. Killian Parish, Mission Viejo, CA

* [Purpose](#purpose)
* [Usage](#usage)
* [Technical Documentation](#technical-documentation)
* [Modules](#modules)
  * [app.py](#appy)
  * [audio.py](#audio)
  * [events.py](#events)
  * [killian_data.py](#killian_data)
  * [session.py](#session)
* [Classes](#classes)
* [Back End](#back-end)

### Purpose
This skill is intended for parishioners of St. Killian, Mission Viejo, with access to Amazon Alexa-enabled devices.

The skill provides multiple conveniences, including the ability to determine Mass times as well as Confession being held at St. Killian, the parish office phone number, calendar events, and even the ability to playback any pre-recorded homilies or speeches that were given and recorded at St. Killian parish.  These will be played back with the Amazon AudioPlayer.  The skill can also issue reminders 30 minutes prior to Mass, reminding parishioners to leave on time; this feature requires the user to grant permissions to the skill to do so, which can be done easily through a card served to the Alexa app on their handheld device, or at [https://alexa.amazon.com](https://alexa.amazon.com "Browser-based version of the Alexa App").

### Usage
Currently, the skill is configured to support the following sample phrases:
 
* Alexa, open Saint Killian
* When is the next mass
* When is mass on Sunday
* When is confession
* What is on the calendar
* Play the latest homily
* Remind me to go to mass
* What is the parish phone number

As mentioned above, permissions need to be granted in order to make use of the Reminders.  Additionally, the device will need to support AudioPlayer protocols in order to make use of the audio playback (I believe all Echo devices support this, although Alexa via the browser does not).

### Technical Documentation
This skill is written in **Python v3.7**, hoted by AWS Lambda.  It interfaces with **DynamoDB** as well as **AWS S3**, and therefore permissions to access both are required via **AWS IAM**.

The skill makes use of **ask_sdk** (_v. 1.10.2 at the time of initial authoring_), and therefore the `SkillBuilder()` class.  `app.py` serves as the entry point for the lambda function.

#### Modules
Several 3rd party packages are included in this installation. The following represent the custom files comprising this skill.

**NOTE!** - One change to the ask_sdk was required in `ask_sdk_core/attributes_manager.py` to allow for `updated_handler` to point to a new intent handler _absent any session variables_. (commit `a24ca20`) This was not allowed by the standard Amazon distribution.

##### app.py
* This serves as the entry point to the lambda function.  It contains all intent/request handlers as well as the SkillBuilder.  Ideally, all logic that determines appropriate responses would be moved out of this file, although in v1.0, some logic exists as functions for basic requests.

##### audio.py
* This file contains all things that utilize the AudioPlayer directives. At the moment, this is just Homilies, but in the future may include Presentations or even Masses, should they be recorded in their entirety.

##### events.py
* This module contains logic for crafting responses for event-like things such as calendar events, Masses, Confession, etc. Each of things things is represented by an object which has methods representing requests that one might make of the thing -- _getNextMass_ or _getNextConfession_, etc.

##### killian_data.py
* This module contains an object called KillianDataManager which is responsible for retrieving data from the DynamoDb database or populating those responses with defaults. Additionally it is the object that commits data to the database. Most of the time, data fetched is then massaged into valid datetime objects, or as lists in correct sort order (which may be alphabetical, or by date, or date relative to `datetime.now()`).

##### session.py
* This is an insanely useful module containing KillianUserSession which makes sense of incoming handler_input from Alexa, populating properties with data extracted from various request_envelopes or environment contexts. It also provides a property for each slot which provides conveniences such as direct access to its value, and a `status` which can be queried to see if it's `None`.  Simply passing a handler_input will immediately populate things like userId, and trigger a database lookup for persistent attributes such as `lastTrack` and `lastToken` (useful for certain AudioPlayer directives).

#### Classes
* coming soon.

#### Back End
* coming soon.
