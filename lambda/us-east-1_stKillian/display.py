###############################################################################
# Copywrite Allen Stetson (allen.stetson@gmail.com) with permissions for
# authorized representitives of St. Killian Parish, Mission Viejo, CA.
###############################################################################
"""Module for assembling display directives."""

# =============================================================================
# Imports
# =============================================================================
# ASK imports
from ask_sdk_model.interfaces.display.render_template_directive import RenderTemplateDirective
from ask_sdk_model.interfaces.display.body_template2 import BodyTemplate2
from ask_sdk_model.interfaces.display.text_content import TextContent
from ask_sdk_model.interfaces.display.image import Image as DisplayImage
from ask_sdk_model.interfaces.display.image_instance import ImageInstance
from ask_sdk_model.interfaces.display.plain_text import PlainText
from ask_sdk_model.interfaces.display.rich_text import RichText

class Directive:
    def __init__(self, mainUrl=None, backgroundUrl=None, title=None, text=None):
        self.mainUrl = mainUrl
        self.backgroundUrl = backgroundUrl
        self.title = title
        self.text = text

    def getDirective(self):
        mainImageInstance = ImageInstance(
            url=self.mainUrl
            #size=ask_sdk_model.interfaces.display.image_size.ImageSize(),
            #width_pixels=int,
            #height_pixels=int
        )
        mainImage = DisplayImage(
            content_description="Main image",
            sources = [mainImageInstance]
        )
        backgroundImageInstance = ImageInstance(
            url=self.backgroundUrl
        )
        backgroundImage = DisplayImage(
            content_description="Background image",
            sources = [backgroundImageInstance]
        )
        textContent = TextContent(
            primary_text=RichText(text=self.text),
            #secondary_text=PlainText(text="secondary text"),
            #tertiary_text=PlainText(text="tertiary text")
        )
        bodyTemplate = BodyTemplate2(
            background_image=backgroundImage,
            image=mainImage,
            title="St. Killian - " + self.title,
            text_content=textContent
        )
        displayDirective = RenderTemplateDirective(template=bodyTemplate)
        return displayDirective
