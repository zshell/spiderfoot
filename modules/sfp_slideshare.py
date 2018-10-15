#-------------------------------------------------------------------------------
# Name:         sfp_slideshare
# Purpose:      Query SlideShare for name and location information.
#
# Author:      Brendan Coles <bcoles@gmail.com>
#
# Created:     2018-10-15
# Copyright:   (c) Brendan Coles 2018
# Licence:     GPL
#-------------------------------------------------------------------------------

import re
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_slideshare(SpiderFootPlugin):
    """SlideShare:Footprint,Investigate,Passive:Social Media::Gather name and location from SlideShare profiles."""

    # Default options
    opts = { 
    }

    # Option descriptions
    optdescs = {
    }

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.__dataSource__ = "SlideShare"
        self.results = dict()

        for opt in userOpts.keys():
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return [ "SOCIAL_MEDIA" ]

    # What events this module produces
    def producedEvents(self):
        return [ "HUMAN_NAME", "GEOINFO" ]

    # Extract meta property contents from HTML
    def extractMeta(self, meta_property, html):
        return re.findall(r'<meta property="' + meta_property + '"\s+content="(.+)" />', html)

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        if eventData in self.results:
            return None
        else:
            self.results[eventData] = True

        self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

        # Retrieve profile
        network = eventData.split(": ")[0]
        name = eventData.split(": ")[1]

        if not network == "SlideShare":
            self.sf.debug("Skipping social network profile, " + name + ", as not a SlideShare profile")
            return None

        res = self.sf.fetchUrl("https://slideshare.net/" + name, timeout=self.opts['_fetchtimeout'], 
                               useragent=self.opts['_useragent'])

        if res['content'] is None:
            return None

        # Check if the profile is valid and extract name
        human_name = self.extractMeta('slideshare:name', res['content'])

        if human_name is None:
            self.sf.debug(name + " is not a valid SlideShare profile")
            return None

        e = SpiderFootEvent("HUMAN_NAME", human_name[0], self.__name__, event)
        self.notifyListeners(e)

        # Retrieve location (country)
        location = self.extractMeta('slideshare:location', res['content'])

        if location is None:
            return None

        if len(location[0]) < 3 or len(location[0]) > 100:
            self.sf.debug("Skipping likely invalid location.")
            return None

        e = SpiderFootEvent("GEOINFO", location[0], self.__name__, event)
        self.notifyListeners(e)

# End of sfp_slideshare class
