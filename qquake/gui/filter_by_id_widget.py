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
import re

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QFileDialog
from qgis.PyQt.QtXml import QDomDocument

from qgis.core import (
    QgsSettings,
    QgsNetworkAccessManager
)
from qgis.PyQt.QtCore import (
    QDir,
    QUrl,
    pyqtSignal
)
from qgis.PyQt.QtNetwork import QNetworkRequest


from qquake.gui.gui_utils import GuiUtils
from qquake.gui.output_table_options_dialog import OutputTableOptionsDialog
from qquake.services import SERVICE_MANAGER
from qquake.fetcher import Fetcher

FORM_CLASS, _ = uic.loadUiType(GuiUtils.get_ui_file_path('filter_by_id_widget_base.ui'))


class FilterByIdWidget(QWidget, FORM_CLASS):
    changed = pyqtSignal()

    def __init__(self, iface, service_type, parent=None):
        """Constructor."""
        super().__init__(parent)

        self.setupUi(self)

        self.radio_single_event.toggled.connect(self._enable_widgets)
        self.radio_multiple_events.toggled.connect(self._enable_widgets)
        self.radio_basic_output.toggled.connect(self._enable_widgets)
        self.radio_extended_output.toggled.connect(self._enable_widgets)
        self.radio_contributor.toggled.connect(self._enable_widgets)

        self.button_refresh_contributors.clicked.connect(self._refresh_contributors)

        self._enable_widgets()

        self.output_table_options_button.clicked.connect(self._output_table_options)

        self.service_type = None
        self.service_id = None
        self.set_service_type(service_type)
        self.output_fields = None
        self.service_config = {}

        self.radio_single_event.toggled.connect(self.changed)
        self.edit_event_id.textChanged.connect(self.changed)
        self.event_ids_edit.textChanged.connect(self.changed)
        self.radio_basic_output.toggled.connect(self.changed)
        self.radio_extended_output.toggled.connect(self.changed)
        self.radio_contributor.toggled.connect(self.changed)
        self.edit_contributor_id.currentTextChanged.connect(self.changed)
        self.button_import_from_file.clicked.connect(self.load_from_file)

    def is_valid(self):
        if self.radio_single_event.isChecked():
            return bool(self.edit_event_id.text())
        elif self.radio_multiple_events.isChecked():
            return bool(self.event_ids_edit.toPlainText())
        elif self.radio_contributor.isChecked():
            return bool(self.edit_contributor_id.currentText())
        return False

    def set_service_type(self, service_type):
        self.service_type = service_type

    def set_service_id(self, service_id):
        self.service_id = service_id
        config = SERVICE_MANAGER.service_details(self.service_type, self.service_id)
        if 'fields' in config['default']:
            self.output_fields = config['default']['fields']

        self.service_config = SERVICE_MANAGER.service_details(self.service_type, self.service_id)

        if not self.service_config['settings'].get('outputtext', False):
            if self.radio_basic_output.isChecked():
                self.radio_extended_output.setChecked(True)
            self.radio_basic_output.setEnabled(False)
        else:
            self.radio_basic_output.setEnabled(True)

        if not self.service_config['settings'].get('outputxml', False):
            if self.radio_extended_output.isChecked():
                self.radio_basic_output.setChecked(True)
            self.radio_extended_output.setEnabled(False)
        else:
            self.radio_extended_output.setEnabled(True)

        if not self.service_config['settings'].get('querycontributorid'):
            if self.radio_contributor.isChecked():
                self.radio_single_event.setChecked(True)
            self.radio_contributor.setEnabled(False)
        else:
            self.radio_contributor.setEnabled(True)

        if self.radio_contributor.isChecked() and self.service_config['settings'].get('querycontributor'):
            self.button_refresh_contributors.setEnabled(True)
        else:
            self.button_refresh_contributors.setEnabled(False)

    def restore_settings(self, prefix):
        s = QgsSettings()

        if self.service_id:
            service_config = SERVICE_MANAGER.service_details(self.service_type, self.service_id)
        else:
            service_config = None

        self.edit_event_id.setText(s.value('/plugins/qquake/{}_single_event_id'.format(prefix), '', str))
        self.edit_contributor_id.setCurrentText(s.value('/plugins/qquake/{}_contributor_id'.format(prefix), '', str))
        if s.value('/plugins/qquake/{}_single_event_checked'.format(prefix), True, bool):
            self.radio_single_event.setChecked(True)
        if s.value('/plugins/qquake/{}_multi_event_checked'.format(prefix), True, bool):
            self.radio_multiple_events.setChecked(True)
        if s.value('/plugins/qquake/{}_contributor_checked'.format(prefix), True, bool):
            if self.radio_contributor.isEnabled():
                self.radio_contributor.setChecked(True)
            else:
                self.radio_single_event.setChecked(True)

        if not service_config or service_config['settings'].get('outputtext', False):
            self.radio_basic_output.setChecked(
                s.value('/plugins/qquake/{}_single_event_basic_checked'.format(prefix), True, bool))

        if not service_config or service_config['settings'].get('outputxml', False):
            self.radio_extended_output.setChecked(
                s.value('/plugins/qquake/{}_single_event_extended_checked'.format(prefix), False, bool))

    def save_settings(self, prefix):
        s = QgsSettings()
        s.setValue('/plugins/qquake/{}_single_event_id'.format(prefix), self.edit_event_id.text())
        s.setValue('/plugins/qquake/{}_single_event_checked'.format(prefix), self.radio_single_event.isChecked())
        s.setValue('/plugins/qquake/{}_multi_event_checked'.format(prefix), self.radio_multiple_events.isChecked())
        s.setValue('/plugins/qquake/{}_contributor_checked'.format(prefix), self.radio_contributor.isChecked())
        s.setValue('/plugins/qquake/{}_contributor_id'.format(prefix), self.edit_contributor_id.currentText())
        s.setValue('/plugins/qquake/{}_single_event_basic_checked'.format(prefix), self.radio_basic_output.isChecked())
        s.setValue('/plugins/qquake/{}_single_event_extended_checked'.format(prefix), self.radio_extended_output.isChecked())

    def _enable_widgets(self):
        for w in [self.label_event_id,
                  self.edit_event_id]:
            w.setEnabled(self.radio_single_event.isChecked())

        for w in [self.multi_event_widget]:
            w.setEnabled(self.radio_multiple_events.isChecked())

        for w in [self.edit_contributor_id, self.label_contributor_id]:
            w.setEnabled(self.radio_contributor.isChecked())

        if self.radio_contributor.isChecked() and self.service_config['settings'].get('querycontributor'):
            self.button_refresh_contributors.setEnabled(True)
        else:
            self.button_refresh_contributors.setEnabled(False)

        self.output_table_options_button.setEnabled(self.radio_extended_output.isChecked())

    def _output_table_options(self):
        dlg = OutputTableOptionsDialog(self.service_type, self.service_id, self.output_fields, self)
        if dlg.exec_():
            self.output_fields = dlg.selected_fields()
            self.changed.emit()

    def contributor_id(self):
        return self.edit_contributor_id.currentText() if self.radio_contributor.isChecked() else None

    def ids(self):
        if self.radio_multiple_events.isChecked():
            id_text = self.event_ids_edit.toPlainText()
            return self.parse_multi_input(id_text)
        elif self.radio_contributor.isChecked():
            return None
        else:
            return [self.edit_event_id.text()]

    @staticmethod
    def parse_multi_input(text):
        return [l.strip() for l in re.split(r'[,\n]', text) if l.strip()]

    def load_from_file(self):
        file, _ = QFileDialog.getOpenFileName(self, self.tr('Import Event IDs from File'), QDir.homePath(), 'Text Files (*.*)')
        if not file:
            return

        with open(file, 'rt') as f:
            text = '\n'.join(f.readlines())
            self.event_ids_edit.setPlainText('\n'.join(self.parse_multi_input(text)))

    def output_type(self):
        return Fetcher.BASIC if self.radio_basic_output.isChecked() else Fetcher.EXTENDED

    def _refresh_contributors(self):
        url = SERVICE_MANAGER.get_contributor_endpoint(self.service_type, self.service_id)
        if not url:
            return

        self.button_refresh_contributors.setEnabled(False)
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)

        reply = QgsNetworkAccessManager.instance().get(request)

        reply.finished.connect(lambda r=reply: self._reply_finished(r))

    def _reply_finished(self, reply):
        self.button_refresh_contributors.setEnabled(True)

        content = reply.readAll()
        if not content:
            return

        self.edit_contributor_id.clear()

        doc = QDomDocument()
        doc.setContent(content)
        contributor_elements = doc.elementsByTagName('Contributor')
        for e in range(contributor_elements.length()):
            contributor_element = contributor_elements.at(e).toElement()
            self.edit_contributor_id.addItem(contributor_element.text())

