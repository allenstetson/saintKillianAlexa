# saintKillianAlexa
Alexa skill for St. Killian Parish, Mission Viejo, CA

![](./kilian-celtic-logo.jpg "St. Killian - Alexa skill")

* [Purpose](#purpose)
* [Usage](#usage)
* [Technical Documentation](#technical-documentation)
* [Modules](#modules)
  * [app.py](#appy)
  * [audio.py](#audio)
  * [display.py](#display)
  * [events.py](#events)
  * [kilian_data.py](#kilian_data)
  * [session.py](#session)
* [Back End](#back-end)
* [Future Work](#future-work)

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
* Help

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

##### display.py
* This file contains a Display Directive template for convenience; it wraps incoming text in sdk_model_interfaces.display text, and assembles proper DisplayImages for incoming URLs. Finally, it adds "Saint Killian - " to the display title, and returns a finished Directive.

##### events.py
* This module contains logic for crafting responses for event-like things such as calendar events, Holy Days, Masses, Confession, etc. Each of things things is represented by an object which has methods representing requests that one might make of the thing -- _getNextMass_ or _getNextConfession_, etc.

##### kilian_data.py
* This module contains an object called KillianDataManager which is responsible for retrieving data from the DynamoDb database or populating those responses with defaults. Additionally it is the object that commits data to the database. Most of the time, data fetched is then massaged into valid datetime objects, or as lists in correct sort order (which may be alphabetical, or by date, or date relative to `datetime.now()`).

##### session.py
* This is an insanely useful module containing KillianUserSession which makes sense of incoming handler_input from Alexa, populating properties with data extracted from various request_envelopes or environment contexts. It also provides a property for each slot which provides conveniences such as direct access to its value, and a `status` which can be queried to see if it's `None`.  Simply passing a handler_input will immediately populate things like userId, and trigger a database lookup for persistent attributes such as `lastTrack` and `lastToken` (useful for certain AudioPlayer directives).

#### Back End
* This code is hosted in **AWS Lambda**. The Lambda function has proper **IAM** permissions which allow it access to **S3** and **DynamoDB**.  Within the S3 bucket are audio tracks, which we purchased legally through PremiumBeat.com (see invoice submitted 8/9/2019) and images (also obtained legally). These URLs are currently hard-coded for playback or display under certain circumstances. In Dynamo, all _Events_ are recorded within, including recurring mass days, holy days, calendar events, confessions.  Holy days have a date associated with them **which needs manual updates for each year!**. They can also have times associated, although if those times are missing, then normal mass times for the day of the week on which it falls will be reported. These times have a mechanism called **massMode** which can be set to "supplement" (default), or "replace"; if "supplement", then any times for that holy day will be reported _in addition to_ the normal times for that weekday.  If "replace", then only the times assigned to that holy day will be reported.  This makes it easy to override all masses on, say Christmas, with a custom set of times; and it makes it easy to leave normal masses in place for, say, Feast of Saint Joeseph.

The Parish Office phone number is also included in Dynamo, and eventually, recordings from mass or guest speakers will be there, too.

Logs can be found through **CloudWatch**, and metrics are gathered which can be accessed through the **Alexa Skills Kit Developer Console**.

Access to the back end is highly restricted, and permissions must be explicitly granted by the owner -- and if you don't know the owner, then you probably shouldn't be messing with the back end. Contact Saint Killian parish office for any assistance of this nature.

The back end is currently hosted for free based on the $100 monthly credits earned through customer interaction and awarded by Amazon.

#### Future Work
* Once recorded homilies come online, we will need to store them in Dynamo with metadata including their S3 URL, not hard-coded for playback.
* The calendar invocation (as of v1.0.0), simply plays a "Coming soon" audio track. Once a shared calendar is set up, with an API, logic must be added to query the calendar, report the results, and set up reminders for events.
* "When is the next holy day" -- should be easily implemented, given all that is currently available.
* Announcements framework for announcing big events, fundraisers, parties, etc upon initial startup.
* Holiday greetings ("Blessed Christmas from Saint Killian Parish", etc.)
* Personal greetings recorded by our clergy and/or staff.
* Web app for managing masses and holy days (_Very Important!_)
* Web app for managing events (_Important_)
* Web app for uploading recorded homilies, etc (_Important)
