# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QQuakeDialog
                                 A QGIS plugin
 QQuake plugin to download seismologic data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-11-20
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Faunalia
        email                : matteo.ghetta@faunalia.eu
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

import os
import json

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QSizePolicy,
    QVBoxLayout
)
from qgis.PyQt.QtCore import (
    Qt,
    QDate,
    QDateTime
)

from qgis.core import (
    Qgis,
    QgsProject,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsSettings,
    QgsCoordinateTransform,
    QgsCsException
)
from qgis.gui import (
    QgsGui,
    QgsMapToolExtent,
    QgsMapToolEmitPoint,
    QgsMessageBar
)

from qquake.qquake_defs import (
    fdsn_events_capabilities,
    MAX_LON_LAT
)

from qquake.fetcher import Fetcher
from qquake.output_table_options_dialog import OutputTableOptionsDialog
from qquake.filter_parameter_widget import FilterParameterWidget

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qquake_dialog_base.ui'))

CONFIG_SERVICES_PATH = os.path.join(
    os.path.dirname(__file__),
    'config',
    'config.json')

with open(CONFIG_SERVICES_PATH, 'r') as f:
    CONFIG_SERVICES = json.load(f)


class QQuakeDialog(QDialog, FORM_CLASS):

    def __init__(self, iface, parent=None):
        """Constructor."""
        super().__init__(parent)

        self.setupUi(self)

        self.fsdn_event_filter = FilterParameterWidget(iface)
        vl = QVBoxLayout()
        vl.addWidget(self.fsdn_event_filter)
        self.fsdn_event_filter_container.setLayout(vl)

        self.message_bar = QgsMessageBar()
        self.message_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.insertWidget(0, self.message_bar)

        self.url_text_browser.viewport().setAutoFillBackground(False)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr('Fetch Data'))
        self.button_box.rejected.connect(self._save_settings)

        self.iface = iface

        # fill the FDSN listWidget with the dictionary keys
        self.fdsn_event_list.addItems(CONFIG_SERVICES['fdsnevent'].keys())
        self.fdsn_event_list.setCurrentRow(0)

        # fill the FDSN listWidget with the dictionary keys
        self.fdsn_macro_list.addItems(CONFIG_SERVICES['macroseismic'].keys())
        self.fdsn_macro_list.setCurrentRow(0)

        # OGC
        self.ogc_services = {
            'Web Map Services (WMS)': 'wms',
            'Web Feature Services (WFS)': 'wfs'
        }
        self.ogc_combo.addItems(self.ogc_services)
        self.ogc_combo.currentIndexChanged.connect(self.refreshOgcWidgets)

        # connect to refreshing function to refresh the UI depending on the WS
        self.refreshFdsnEventWidgets()
        self.refreshFdsnMacroseismicWidgets()

        # change the UI parameter according to the web service chosen
        self.fdsn_event_list.currentRowChanged.connect(
            self.refreshFdsnEventWidgets)
        self.fdsn_macro_list.currentRowChanged.connect(
            self.refreshFdsnMacroseismicWidgets)

        self.fsdn_event_filter.changed.connect(self._refresh_url)
        self.fdsn_event_list.currentRowChanged.connect(self._refresh_url)
        self.fdsn_macro_list.currentRowChanged.connect(self._refresh_url)

        self.button_box.accepted.connect(self._getEventList)

        self.fetcher = None

        QgsGui.enableAutoGeometryRestore(self)

        self._restore_settings()
        self._refresh_url()

    def closeEvent(self, e):
        self._save_settings()
        super().closeEvent(e)

    def _save_settings(self):
        s = QgsSettings()
        # FDSN Event
        s.setValue('/plugins/qquake/fdsn_event_last_event_service', self.fdsn_event_list.currentItem().text())
        s.setValue('/plugins/qquake/fdsn_event_last_event_start_date', self.fdsn_event_start_date.dateTime())
        s.setValue('/plugins/qquake/fdsn_event_last_event_end_date', self.fdsn_event_end_date.dateTime())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_magnitude', self.fdsn_event_min_magnitude.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_magnitude', self.fdsn_event_max_magnitude.value())

        s.setValue('/plugins/qquake/fdsn_event_last_event_extent_enabled', self.limit_extent_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_extent_rect', self.radio_rectangular_area.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_extent_circle', self.radio_circular_area.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_lat_checked', self.lat_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_lat', self.lat_min_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_lat_checked', self.lat_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_lat', self.lat_max_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_long_checked', self.long_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_long', self.long_min_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_long_checked', self.long_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_long', self.long_max_spinbox.value())

        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_long', self.circular_long_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_lat', self.circular_lat_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_radius_min_checked',
                   self.radius_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_radius_max_checked',
                   self.radius_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_min_radius', self.radius_min_spinbox.value())
        s.setValue('/plugins/qquake/fdsn_event_last_event_circle_max_radius', self.radius_max_spinbox.value())

        s.setValue('/plugins/qquake/fdsn_event_last_event_min_time_checked', self.min_time_check.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_time_checked', self.max_time_check.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_min_mag_checked', self.min_mag_check.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_event_max_mag_checked', self.max_mag_check.isChecked())

        s.setValue('/plugins/qquake/fdsn_event_last_output_preferred_origins_only',
                   self.output_preferred_origins_only_check.isChecked())
        s.setValue('/plugins/qquake/fdsn_event_last_output_preferred_magnitude_only',
                   self.output_preferred_magnitudes_only_check.isChecked())

    def _restore_settings(self):
        s = QgsSettings()
        last_service = s.value('/plugins/qquake/fdsn_event_last_event_service')
        if last_service is not None:
            self.fdsn_event_list.setCurrentItem(
                self.fdsn_event_list.findItems(last_service, Qt.MatchContains)[0])
        self.fsdn_event_filter.restore_settings()

    def get_fetcher(self):
        """
        Returns a quake fetcher corresponding to the current dialog settings
        """
        return Fetcher(event_service=self.fdsn_event_list.currentItem().text(),
                       event_start_date=self.fsdn_event_filter.start_date(),
                       event_end_date=self.fsdn_event_filter.end_date(),
                       event_min_magnitude=self.fsdn_event_filter.min_magnitude(),
                       event_max_magnitude=self.fsdn_event_filter.max_magnitude(),
                       limit_extent_rect=self.fsdn_event_filter.extent_rect(),
                       min_latitude=self.fsdn_event_filter.min_latitude(),
                       max_latitude=self.fsdn_event_filter.max_latitude(),
                       min_longitude=self.fsdn_event_filter.min_longitude(),
                       max_longitude=self.fsdn_event_filter.max_longitude(),
                       limit_extent_circle=self.fsdn_event_filter.limit_extent_circle(),
                       circle_latitude=self.fsdn_event_filter.circle_latitude(),
                       circle_longitude=self.fsdn_event_filter.circle_longitude(),
                       circle_min_radius=self.fsdn_event_filter.circle_min_radius(),
                       circle_max_radius=self.fsdn_event_filter.circle_max_radius(),
                       )

    def _refresh_url(self):
        fetcher = self.get_fetcher()
        self.url_text_browser.setText('<a href="{0}">{0}</a>'.format(fetcher.generate_url()))

    def refreshFdsnEventWidgets(self):
        """
        Refreshing the FDSN-Event UI depending on the WS chosen
        """

        datestart = QDateTime.fromString(
            CONFIG_SERVICES['fdsnevent'][self.fdsn_event_list.currentItem(
            ).text()]['default']['datestart'],
            Qt.ISODate
        )

        # if the dateend is not set in the config.json set the date to NOW
        try:
            dateend = QDateTime.fromString(
                CONFIG_SERVICES['fdsnevent'][self.fdsn_event_list.currentItem(
                ).text()]['default']['dateend'],
                Qt.ISODate
            )
        except KeyError:
            dateend = QDate.currentDate()

        self.fsdn_event_filter.set_date_range_limits(datestart, dateend)

        box = CONFIG_SERVICES['boundingboxpredefined'][CONFIG_SERVICES['fdsnevent'][self.fdsn_event_list.currentItem(
        ).text()]['default']['boundingboxpredefined']]['boundingbox']
        self.fsdn_event_filter.set_extent_limit(box)

    def refreshFdsnMacroseismicWidgets(self):
        """
        Refreshing the FDSN-Macroseismic UI depending on the WS chosen
        """

        datestart = QDateTime.fromString(
            CONFIG_SERVICES['macroseismic'][self.fdsn_macro_list.currentItem(
            ).text()]['default']['datestart'],
            Qt.ISODate
        )

        # if the dateend is not set in the config.json set the date to NOW
        try:
            dateend = QDateTime.fromString(
                CONFIG_SERVICES['macroseismic'][self.fdsn_macro_list.currentItem(
                ).text()]['default']['dateend'],
                Qt.ISODate
            )
        except KeyError:
            dateend = QDate.currentDate()

        # set DateTime Widget START according to the listWidget choice
        self.fdsn_macro_start_date.setMinimumDateTime(datestart)
        self.fdsn_macro_start_date.setMaximumDateTime(dateend)
        self.fdsn_macro_start_date.setDateTime(datestart)

        # set DateTime Widget END according to the listWidget choice
        self.fdsn_macro_end_date.setMinimumDateTime(datestart)
        self.fdsn_macro_end_date.setMaximumDateTime(dateend)
        # just make a week difference from START date
        self.fdsn_macro_end_date.setDateTime(datestart.addDays(7))

        self.fdsn_macro_ExtentGroupBox.setOutputExtentFromUser(
            QgsRectangle(
                *CONFIG_SERVICES['boundingboxpredefined'][
                    CONFIG_SERVICES['macroseismic'][self.fdsn_macro_list.currentItem(
                    ).text()]['default']['boundingboxpredefined']]['boundingbox']
            ),
            QgsCoordinateReferenceSystem('EPSG:4326')
        )

    def refreshOgcWidgets(self):
        """
        read the ogc_combo and fill it with the services
        """
        self.ogc_list.clear()
        ogc_selection = self.ogc_services[self.ogc_combo.currentText()]
        self.ogc_list.addItems(CONFIG_SERVICES[ogc_selection].keys())
        self.ogc_list.setCurrentRow(0)

    def _getEventList(self):
        """
        read the event URL and convert the response in a list
        """
        if self.fetcher:
            # TODO - cancel current request
            return

        self.fetcher = self.get_fetcher()
        self.fetcher.progress.connect(self.progressBar.setValue)
        self.fetcher.finished.connect(self._fetcher_finished)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr('Fetching'))
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        self.fetcher.fetch_data()

    def _fetcher_finished(self):
        self.progressBar.reset()
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr('Fetch Data'))
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

        layers = []
        layers.append(self.fetcher.create_event_layer())
        events_count = layers[0].featureCount()
        if not self.output_preferred_origins_only_check.isChecked():
            layers.append(self.fetcher.create_origin_layer())
        if not self.output_preferred_magnitudes_only_check.isChecked():
            layers.append(self.fetcher.create_magnitude_layer())

        max_feature_count = 0
        for l in layers:
            max_feature_count = max(max_feature_count, l.featureCount())

        service_limit = self.fetcher.service_config['settings'].get('querylimitmaxentries', None)
        self.message_bar.clearWidgets()
        if service_limit is not None and max_feature_count >= service_limit:
            self.message_bar.pushMessage(self.tr("Query exceeded the service's result limit"), Qgis.Critical, 0)
        elif max_feature_count > 500:
            self.message_bar.pushMessage(
                self.tr("Query returned a large number of results ({})".format(max_feature_count)), Qgis.Warning, 0)
        elif max_feature_count == 0:
            self.message_bar.pushMessage(
                self.tr("Query returned no results - possibly parameters are invalid for this service"), Qgis.Critical,
                0)
        else:
            self.message_bar.pushMessage(
                self.tr("Query returned {} events").format(events_count), Qgis.Info, 0)

        self.fetcher.deleteLater()
        self.fetcher = None

        if max_feature_count > 0:
            QgsProject.instance().addMapLayers(layers)
