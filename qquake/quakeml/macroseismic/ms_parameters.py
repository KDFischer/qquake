# -*- coding: utf-8 -*-
"""QuakeML element

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = 'Original authors: Mario Locati, Roberto Vallone, Matteo Ghetta, Nyall Dawson'
__date__ = '29/01/2020'
__copyright__ = 'Istituto Nazionale di Geofisica e Vulcanologia (INGV)'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from typing import List

from qgis.PyQt.QtXml import QDomElement

from ..element import QuakeMlElement
from .ms_event import MsEvent


class MsParameters(QuakeMlElement):
    """
    MacroseismicParameters
    """

    def __init__(self,
                 publicID,
                 macroseismicEvent: List):
        self.publicID = publicID
        self.macroseismicEvent = macroseismicEvent  # one to many

    @staticmethod
    def from_element(element: QDomElement) -> 'MsParameters':
        """
        Constructs MsParameters from a DOM element
        """
        from ..element_parser import ElementParser  # pylint: disable=import-outside-toplevel
        parser = ElementParser(element)

        events = []
        event_node = element.firstChildElement('ms:macroseismicEvent')
        while not event_node.isNull():
            events.append(MsEvent.from_element(event_node))
            event_node = event_node.nextSiblingElement('ms:macroseismicEvent')

        return MsParameters(publicID=parser.string('publicID', is_attribute=True, optional=False),
                            macroseismicEvent=events)
