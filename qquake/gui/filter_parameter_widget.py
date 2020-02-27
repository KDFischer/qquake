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
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import (
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCsException,
    QgsSettings
)
from qgis.gui import (
    QgsMapToolExtent,
    QgsMapToolEmitPoint,
)

from qquake.gui.gui_utils import GuiUtils
from qquake.gui.output_table_options_dialog import OutputTableOptionsDialog

FORM_CLASS, _ = uic.loadUiType(GuiUtils.get_ui_file_path('filter_parameter_widget_base.ui'))


class FilterParameterWidget(QWidget, FORM_CLASS):
    changed = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super().__init__(parent)

        self.setupUi(self)

        self.iface = iface
        self.previous_map_tool = None
        self.extent_tool = None

        self.set_extent_from_canvas_extent(self.iface.mapCanvas().extent())
        self.set_center_from_canvas_point(self.iface.mapCanvas().extent().center())

        self.fdsn_event_start_date.dateChanged.connect(self._refresh_date)
        self.min_time_check.toggled.connect(self.changed)
        self.fdsn_event_start_date.dateChanged.connect(self.changed)
        self.max_time_check.toggled.connect(self.changed)
        self.fdsn_event_end_date.dateChanged.connect(self.changed)
        self.min_mag_check.toggled.connect(self.changed)
        self.fdsn_event_min_magnitude.valueChanged.connect(self.changed)
        self.max_mag_check.toggled.connect(self.changed)
        self.fdsn_event_max_magnitude.valueChanged.connect(self.changed)
        self.lat_min_spinbox.valueChanged.connect(self.changed)
        self.lat_max_spinbox.valueChanged.connect(self.changed)
        self.long_min_spinbox.valueChanged.connect(self.changed)
        self.long_max_spinbox.valueChanged.connect(self.changed)
        self.lat_min_checkbox.toggled.connect(self.changed)
        self.lat_max_checkbox.toggled.connect(self.changed)
        self.long_min_checkbox.toggled.connect(self.changed)
        self.long_max_checkbox.toggled.connect(self.changed)
        self.limit_extent_checkbox.toggled.connect(self.changed)
        self.radio_rectangular_area.toggled.connect(self.changed)
        self.radio_circular_area.toggled.connect(self.changed)
        self.circular_lat_spinbox.valueChanged.connect(self.changed)
        self.circular_long_spinbox.valueChanged.connect(self.changed)
        self.radius_min_checkbox.toggled.connect(self.changed)
        self.radius_max_checkbox.toggled.connect(self.changed)
        self.radius_min_spinbox.valueChanged.connect(self.changed)
        self.radius_max_spinbox.valueChanged.connect(self.changed)
        self.earthquake_max_intensity_greater_check.toggled.connect(self.changed)
        self.earthquake_max_intensity_greater_spin.valueChanged.connect(self.changed)
        self.earthquake_number_mdps_greater_check.toggled.connect(self.changed)
        self.earthquake_number_mdps_greater_spin.valueChanged.connect(self.changed)

        self.rect_extent_draw_on_map.clicked.connect(self.draw_rect_on_map)
        self.circle_center_draw_on_map.clicked.connect(self.draw_center_on_map)

        self.radio_rectangular_area.toggled.connect(self._enable_widgets)
        self.radio_circular_area.toggled.connect(self._enable_widgets)
        self.limit_extent_checkbox.toggled.connect(self._enable_widgets)
        self.lat_min_checkbox.toggled.connect(self._enable_widgets)
        self.lat_max_checkbox.toggled.connect(self._enable_widgets)
        self.long_min_checkbox.toggled.connect(self._enable_widgets)
        self.long_max_checkbox.toggled.connect(self._enable_widgets)
        self.radius_min_checkbox.toggled.connect(self._enable_widgets)
        self.radius_max_checkbox.toggled.connect(self._enable_widgets)
        self.min_time_check.toggled.connect(self._enable_widgets)
        self.max_time_check.toggled.connect(self._enable_widgets)
        self.min_mag_check.toggled.connect(self._enable_widgets)
        self.max_mag_check.toggled.connect(self._enable_widgets)
        self.earthquake_max_intensity_greater_check.toggled.connect(self._enable_widgets)
        self.earthquake_number_mdps_greater_check.toggled.connect(self._enable_widgets)
        self._enable_widgets()

        self.output_table_options_button.clicked.connect(self._output_table_options)

    def set_show_macroseismic_data_options(self, show):
        self.macroseismic_data_group.setVisible(show)
        self.output_preferred_mdp_only_check.setVisible(show)

    def restore_settings(self, prefix):
        s = QgsSettings()
        last_event_start_date = s.value('/plugins/qquake/{}_last_event_start_date'.format(prefix))
        if last_event_start_date is not None:
            self.fdsn_event_start_date.setDateTime(last_event_start_date)
        last_event_end_date = s.value('/plugins/qquake/{}_last_event_end_date'.format(prefix))
        if last_event_end_date is not None:
            self.fdsn_event_end_date.setDateTime(last_event_end_date)
        last_event_min_magnitude = s.value('/plugins/qquake/{}_last_event_min_magnitude'.format(prefix))
        if last_event_min_magnitude is not None:
            self.fdsn_event_min_magnitude.setValue(float(last_event_min_magnitude))
        last_event_max_magnitude = s.value('/plugins/qquake/{}_last_event_max_magnitude'.format(prefix))
        if last_event_max_magnitude is not None:
            self.fdsn_event_max_magnitude.setValue(float(last_event_max_magnitude))
        last_event_extent_enabled = s.value('/plugins/qquake/{}_last_event_extent_enabled'.format(prefix))
        if last_event_extent_enabled is not None:
            self.limit_extent_checkbox.setChecked(bool(last_event_extent_enabled))
        last_event_extent_rect = s.value('/plugins/qquake/{}_last_event_extent_rect'.format(prefix))
        if last_event_extent_rect is not None:
            self.radio_rectangular_area.setChecked(bool(last_event_extent_rect))
        last_event_extent_circle = s.value('/plugins/qquake/{}_last_event_extent_circle'.format(prefix))
        if last_event_extent_circle is not None:
            self.radio_circular_area.setChecked(bool(last_event_extent_circle))
        min_lat_checked = s.value('/plugins/qquake/{}_last_event_min_lat_checked'.format(prefix))
        if min_lat_checked is not None:
            self.lat_min_checkbox.setChecked(bool(min_lat_checked))
        max_lat_checked = s.value('/plugins/qquake/{}_last_event_max_lat_checked'.format(prefix))
        if max_lat_checked is not None:
            self.lat_max_checkbox.setChecked(bool(max_lat_checked))
        min_long_checked = s.value('/plugins/qquake/{}_last_event_min_long_checked'.format(prefix))
        if min_long_checked is not None:
            self.long_min_checkbox.setChecked(bool(min_long_checked))
        max_long_checked = s.value('/plugins/qquake/{}_last_event_max_long_checked'.format(prefix))
        if max_long_checked is not None:
            self.long_max_checkbox.setChecked(bool(max_long_checked))

        min_radius_checked = s.value('/plugins/qquake/{}_last_event_circle_radius_min_checked'.format(prefix))
        if min_radius_checked is not None:
            self.radius_min_checkbox.setChecked(bool(min_radius_checked))
        max_radius_checked = s.value('/plugins/qquake/{}_last_event_circle_radius_max_checked'.format(prefix))
        if max_radius_checked is not None:
            self.radius_max_checkbox.setChecked(bool(max_radius_checked))

        last_event_min_radius = s.value('/plugins/qquake/{}_last_event_circle_min_radius'.format(prefix))
        if last_event_min_radius is not None:
            self.radius_min_spinbox.setValue(float(last_event_min_radius))
        last_event_max_radius = s.value('/plugins/qquake/{}_last_event_circle_max_radius'.format(prefix))
        if last_event_max_radius is not None:
            self.radius_max_spinbox.setValue(float(last_event_max_radius))

        min_time_checked = s.value('/plugins/qquake/{}_last_event_min_time_checked'.format(prefix))
        if min_time_checked is not None:
            self.min_time_check.setChecked(bool(min_time_checked))
        max_time_checked = s.value('/plugins/qquake/{}_last_event_max_time_checked'.format(prefix))
        if max_time_checked is not None:
            self.max_time_check.setChecked(bool(max_time_checked))
        min_mag_checked = s.value('/plugins/qquake/{}_last_event_min_mag_checked'.format(prefix))
        if min_mag_checked is not None:
            self.min_mag_check.setChecked(bool(min_mag_checked))
        max_mag_checked = s.value('/plugins/qquake/{}_last_event_max_mag_checked'.format(prefix))
        if max_mag_checked is not None:
            self.max_mag_check.setChecked(bool(max_mag_checked))

        v = s.value('/plugins/qquake/{}_last_event_max_intensity_greater_checked'.format(prefix))
        if v is not None:
            self.earthquake_max_intensity_greater_check.setChecked(bool(v))
        v = s.value('/plugins/qquake/{}_last_event_max_intensity_greater'.format(prefix))
        if v is not None:
            self.earthquake_max_intensity_greater_spin.setValue(float(v))
        v = s.value('/plugins/qquake/{}_last_event_mdps_greater_checked'.format(prefix))
        if v is not None:
            self.earthquake_number_mdps_greater_check.setChecked(bool(v))
        v = s.value('/plugins/qquake/{}_last_event_mdps_greater'.format(prefix))
        if v is not None:
            self.earthquake_number_mdps_greater_spin.setValue(float(v))

        preferred_origins_only_checked = s.value('/plugins/qquake/{}_last_output_preferred_origins_only'.format(prefix))
        if preferred_origins_only_checked is not None:
            self.output_preferred_origins_only_check.setChecked(bool(preferred_origins_only_checked))
        preferred_magnitudes_only_checked = s.value(
            '/plugins/qquake/{}_last_output_preferred_magnitude_only'.format(prefix))
        if preferred_magnitudes_only_checked is not None:
            self.output_preferred_magnitudes_only_check.setChecked(bool(preferred_magnitudes_only_checked))

        v = s.value('/plugins/qquake/{}_last_output_preferred_mdp_only'.format(prefix))
        if v is not None:
            self.output_preferred_mdp_only_check.setChecked(bool(v))

    def save_settings(self, prefix):
        s = QgsSettings()
        s.setValue('/plugins/qquake/{}_last_event_start_date'.format(prefix), self.fdsn_event_start_date.dateTime())
        s.setValue('/plugins/qquake/{}_last_event_end_date'.format(prefix), self.fdsn_event_end_date.dateTime())
        s.setValue('/plugins/qquake/{}_last_event_min_magnitude'.format(prefix), self.fdsn_event_min_magnitude.value())
        s.setValue('/plugins/qquake/{}_last_event_max_magnitude'.format(prefix), self.fdsn_event_max_magnitude.value())

        s.setValue('/plugins/qquake/{}_last_event_extent_enabled'.format(prefix),
                   self.limit_extent_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_extent_rect'.format(prefix), self.radio_rectangular_area.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_extent_circle'.format(prefix), self.radio_circular_area.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_min_lat_checked'.format(prefix), self.lat_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_min_lat'.format(prefix), self.lat_min_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_max_lat_checked'.format(prefix), self.lat_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_max_lat'.format(prefix), self.lat_max_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_min_long_checked'.format(prefix), self.long_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_min_long'.format(prefix), self.long_min_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_max_long_checked'.format(prefix), self.long_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_max_long'.format(prefix), self.long_max_spinbox.value())

        s.setValue('/plugins/qquake/{}_last_event_circle_long'.format(prefix), self.circular_long_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_circle_lat'.format(prefix), self.circular_lat_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_circle_radius_min_checked'.format(prefix),
                   self.radius_min_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_circle_radius_max_checked'.format(prefix),
                   self.radius_max_checkbox.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_circle_min_radius'.format(prefix), self.radius_min_spinbox.value())
        s.setValue('/plugins/qquake/{}_last_event_circle_max_radius'.format(prefix), self.radius_max_spinbox.value())

        s.setValue('/plugins/qquake/{}_last_event_max_intensity_greater_checked'.format(prefix),
                   self.earthquake_max_intensity_greater_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_max_intensity_greater'.format(prefix),
                   self.earthquake_max_intensity_greater_spin.value())
        s.setValue('/plugins/qquake/{}_last_event_mdps_greater_checked'.format(prefix),
                   self.earthquake_number_mdps_greater_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_mdps_greater'.format(prefix),
                   self.earthquake_number_mdps_greater_spin.value())

        s.setValue('/plugins/qquake/{}_last_event_min_time_checked'.format(prefix), self.min_time_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_max_time_checked'.format(prefix), self.max_time_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_min_mag_checked'.format(prefix), self.min_mag_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_event_max_mag_checked'.format(prefix), self.max_mag_check.isChecked())

        s.setValue('/plugins/qquake/{}_last_output_preferred_origins_only'.format(prefix),
                   self.output_preferred_origins_only_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_output_preferred_magnitude_only'.format(prefix),
                   self.output_preferred_magnitudes_only_check.isChecked())
        s.setValue('/plugins/qquake/{}_last_output_preferred_mdp_only'.format(prefix),
                   self.output_preferred_mdp_only_check.isChecked())

    def set_extent_from_canvas_extent(self, rect):
        ct = QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(),
                                    QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
        try:
            rect = ct.transformBoundingBox(rect)
            self.lat_min_spinbox.setValue(rect.yMinimum())
            self.lat_max_spinbox.setValue(rect.yMaximum())
            self.long_min_spinbox.setValue(rect.xMinimum())
            self.long_max_spinbox.setValue(rect.xMaximum())
        except QgsCsException:
            pass

    def set_center_from_canvas_point(self, point):
        ct = QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(),
                                    QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
        try:
            point = ct.transform(point)
            self.circular_lat_spinbox.setValue(point.y())
            self.circular_long_spinbox.setValue(point.x())
        except QgsCsException:
            pass

    def _enable_widgets(self):
        for w in [self.lat_min_checkbox,
                  self.lat_max_checkbox,
                  self.long_min_checkbox,
                  self.long_max_checkbox,
                  self.lat_min_spinbox,
                  self.lat_max_spinbox,
                  self.long_min_spinbox,
                  self.long_max_spinbox,
                  self.label_rect_lat,
                  self.label_rect_long,
                  self.rect_extent_draw_on_map]:
            w.setEnabled(self.radio_rectangular_area.isChecked() and self.limit_extent_checkbox.isChecked())
        self.lat_min_spinbox.setEnabled(self.lat_min_spinbox.isEnabled() and self.lat_min_checkbox.isChecked())
        self.lat_max_spinbox.setEnabled(self.lat_max_spinbox.isEnabled() and self.lat_max_checkbox.isChecked())
        self.long_min_spinbox.setEnabled(self.long_min_spinbox.isEnabled() and self.long_min_checkbox.isChecked())
        self.long_max_spinbox.setEnabled(self.long_max_spinbox.isEnabled() and self.long_max_checkbox.isChecked())

        for w in [self.circular_lat_spinbox,
                  self.circular_long_spinbox,
                  self.radius_min_checkbox,
                  self.radius_min_spinbox,
                  self.radius_max_checkbox,
                  self.radius_max_spinbox,
                  self.label_circ_center,
                  self.label_circ_radius,
                  self.label_circ_lat,
                  self.label_circ_long,
                  self.circle_center_draw_on_map]:
            w.setEnabled(self.radio_circular_area.isChecked() and self.limit_extent_checkbox.isChecked())
        self.radius_min_spinbox.setEnabled(self.radius_min_spinbox.isEnabled() and self.radius_min_checkbox.isChecked())
        self.radius_max_spinbox.setEnabled(self.radius_max_spinbox.isEnabled() and self.radius_max_checkbox.isChecked())

        self.fdsn_event_start_date.setEnabled(self.min_time_check.isChecked())
        self.fdsn_event_end_date.setEnabled(self.max_time_check.isChecked())
        self.fdsn_event_min_magnitude.setEnabled(self.min_mag_check.isChecked())
        self.fdsn_event_max_magnitude.setEnabled(self.max_mag_check.isChecked())

        self.earthquake_max_intensity_greater_spin.setEnabled(self.earthquake_max_intensity_greater_check.isChecked())
        self.earthquake_number_mdps_greater_spin.setEnabled(self.earthquake_number_mdps_greater_check.isChecked())

    def draw_rect_on_map(self):
        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        if not self.extent_tool:
            self.extent_tool = QgsMapToolExtent(self.iface.mapCanvas())
            self.extent_tool.extentChanged.connect(self.extent_drawn)
            self.extent_tool.deactivated.connect(self.deactivate_tool)
        self.iface.mapCanvas().setMapTool(self.extent_tool)
        self.window().setVisible(False)

    def draw_center_on_map(self):
        self.previous_map_tool = self.iface.mapCanvas().mapTool()
        if not self.extent_tool:
            self.extent_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            self.extent_tool.canvasClicked.connect(self.center_picked)
            self.extent_tool.deactivated.connect(self.deactivate_tool)
        self.iface.mapCanvas().setMapTool(self.extent_tool)
        self.window().setVisible(False)

    def extent_drawn(self, extent):
        self.set_extent_from_canvas_extent(extent)
        self.iface.mapCanvas().setMapTool(self.previous_map_tool)
        self.window().setVisible(True)
        self.previous_map_tool = None
        self.extent_tool = None

    def center_picked(self, point, button):
        self.set_center_from_canvas_point(point)
        self.iface.mapCanvas().setMapTool(self.previous_map_tool)
        self.window().setVisible(True)
        self.previous_map_tool = None
        self.extent_tool = None

    def deactivate_tool(self):
        self.window().setVisible(True)
        self.previous_map_tool = None
        self.extent_tool = None

    def _refresh_date(self):
        """
        Avoids negative date intervals by checking start_date > end_date
        """

        if self.fdsn_event_start_date.dateTime() > self.fdsn_event_end_date.dateTime():
            self.fdsn_event_end_date.setDate(self.fdsn_event_start_date.date())

    def set_date_range_limits(self, date_start, date_end):
        self.fdsn_event_start_date.setMinimumDateTime(date_start)
        self.fdsn_event_start_date.setMaximumDateTime(date_end)
        self.fdsn_event_start_date.setDateTime(date_start)

        if date_start.isValid():
            self.min_time_check.setText(
                self.tr("Start (from {})").format(date_start.toString('yyyy-MM-dd')))
        else:
            self.min_time_check.setText(self.tr("Start"))

        if date_end.isValid():
            self.max_time_check.setText(
                self.tr("End (until {})").format(date_end.toString('yyyy-MM-dd')))
        else:
            self.max_time_check.setText(self.tr("End"))

        self.fdsn_event_end_date.setMinimumDateTime(date_start)
        self.fdsn_event_end_date.setMaximumDateTime(date_end)
        # just make a week difference from START date
        self.fdsn_event_end_date.setDateTime(date_start.addDays(7))

    def set_extent_limit(self, box):
        self.long_min_spinbox.setMinimum(box[0])
        self.long_max_spinbox.setMinimum(box[0])
        self.lat_min_spinbox.setMinimum(box[1])
        self.lat_max_spinbox.setMinimum(box[1])
        self.long_min_spinbox.setMaximum(box[2])
        self.long_max_spinbox.setMaximum(box[2])
        self.lat_min_spinbox.setMaximum(box[3])
        self.lat_max_spinbox.setMaximum(box[3])

    def _output_table_options(self):
        dlg = OutputTableOptionsDialog(self)
        if dlg.exec_():
            pass

    def start_date(self):
        return self.fdsn_event_start_date.dateTime() if self.min_time_check.isChecked() else None

    def end_date(self):
        return self.fdsn_event_end_date.dateTime() if self.max_time_check.isChecked() else None

    def min_magnitude(self):
        return self.fdsn_event_min_magnitude.value() if self.min_mag_check.isChecked() else None

    def max_magnitude(self):
        return self.fdsn_event_max_magnitude.value() if self.max_mag_check.isChecked() else None

    def extent_rect(self):
        return self.limit_extent_checkbox.isChecked() and self.radio_rectangular_area.isChecked()

    def min_latitude(self):
        return self.lat_min_spinbox.value() if self.lat_min_checkbox.isChecked() else None

    def max_latitude(self):
        return self.lat_max_spinbox.value() if self.lat_max_checkbox.isChecked() else None

    def min_longitude(self):
        return self.long_min_spinbox.value() if self.long_min_checkbox.isChecked() else None

    def max_longitude(self):
        return self.long_max_spinbox.value() if self.long_max_checkbox.isChecked() else None

    def limit_extent_circle(self):
        return self.limit_extent_checkbox.isChecked() and self.radio_circular_area.isChecked()

    def circle_latitude(self):
        return self.circular_lat_spinbox.value()

    def circle_longitude(self):
        return self.circular_long_spinbox.value()

    def circle_min_radius(self):
        return self.radius_min_spinbox.value() if self.radius_min_checkbox.isChecked() else None

    def circle_max_radius(self):
        return self.radius_max_spinbox.value() if self.radius_max_checkbox.isChecked() else None

    def earthquake_max_intensity_greater(self):
        return self.earthquake_max_intensity_greater_spin.value() if self.earthquake_max_intensity_greater_check.isChecked() else None

    def earthquake_number_mdps_greater(self):
        return self.earthquake_number_mdps_greater_spin.value() if self.earthquake_number_mdps_greater_check.isChecked() else None

    def output_preferred_magnitudes_only(self):
        return self.output_preferred_magnitudes_only_check.isChecked()

    def output_preferred_origins_only(self):
        return self.output_preferred_origins_only_check.isChecked()

    def output_preferred_mdp_only(self):
        return self.output_preferred_mdp_only_check.isChecked()
