# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QQuake, a QGIS Plugin for Loading Seismological Data From Web Services

 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-11-20
        git sha              : $Format:%H$
        copyright            : Istituto Nazionale di Geofisica e Vulcanologia (INGV)
        email                : mario.locati@ingv.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import abc
from typing import List, Optional, Dict

from qgis.PyQt.QtWidgets import QWidget
from qgis.core import (
    QgsUnitTypes
)


class QABCMeta(abc.ABCMeta, type(QWidget)):
    """
    Meta class that combines ABC and the Qt meta class
    """


class BaseFilterWidget(abc.ABC, metaclass=QABCMeta):
    """
    Base class for filter widgets
    """

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """
        Returns True if the widget state is valid
        """

    @abc.abstractmethod
    def set_service_type(self, service_type: str):
        """
        Sets the associated service type
        """

    @abc.abstractmethod
    def set_service_id(self, service_id: str):
        """
        Sets the associated service ID
        """

    @abc.abstractmethod
    def restore_settings(self, prefix: str):
        """
        Restores widget state from settings
        """

    @abc.abstractmethod
    def save_settings(self, prefix: str):
        """
        Saves widget state to settings
        """

    @abc.abstractmethod
    def output_type(self) -> str:
        """
        Returns the output table type
        """

    @abc.abstractmethod
    def output_fields(self) -> Optional[List[str]]:
        """
        Returns the selected output fields
        """

    @abc.abstractmethod
    def convert_negative_depths(self) -> bool:
        """
        Returns True if negative depths must be converted
        """

    @abc.abstractmethod
    def depth_unit(self) -> QgsUnitTypes.DistanceUnit:
        """
        Returns the associated depth unit
        """

    @abc.abstractmethod
    def selected_styles(self) -> Dict[str, str]:
        """
        Returns a dictionary of the selected styles for the results
        """
