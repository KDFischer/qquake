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
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import (
    QModelIndex,
    Qt
)

from qgis.core import QgsSettings
from qgis.gui import QgsGui

from qquake.gui.gui_utils import GuiUtils
from qquake.gui.simple_node_model import SimpleNodeModel, ModelNode

FORM_CLASS, _ = uic.loadUiType(GuiUtils.get_ui_file_path('output_table_options.ui'))


CONFIG_FIELDS_PATH = os.path.join(
    os.path.dirname(__file__),
    'config',
    'config_fields_fsdnevent.json')

with open(CONFIG_FIELDS_PATH, 'r') as f:
    CONFIG_FIELDS = json.load(f)


class OutputTableOptionsDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle(self.tr('Output Table Options'))

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        QgsGui.enableAutoGeometryRestore(self)

        s = QgsSettings()

        nodes = []
        for key, settings in CONFIG_FIELDS['field_groups'].items():
            parent_node = ModelNode([settings['label']])
            for f in settings['fields']:
                path = f['source'][len('eventParameters>event>'):]
                checked = s.value('/plugins/qquake/output_field_{}'.format(path.replace('>', '_')), True, bool)

                parent_node.addChild(
                    ModelNode(['checked', f['field'], path], checked))
            nodes.append(parent_node)

        self.field_model = SimpleNodeModel(nodes, headers=[self.tr('Include'), self.tr('Field Name'),
                                                           self.tr('QuakeML Source')])
        self.fields_tree_view.setModel(self.field_model)
        self.fields_tree_view.expandAll()

        for r in range(self.field_model.rowCount(QModelIndex())):
            self.fields_tree_view.setFirstColumnSpanned(r, QModelIndex(), True)

        self.reset_fields_button.clicked.connect(self.reset_fields)

    def accept(self):
        s = QgsSettings()
        for r in range(self.field_model.rowCount(QModelIndex())):
            parent = self.field_model.index(r, 0, QModelIndex())
            for rc in range(self.field_model.rowCount(parent)):
                path = self.field_model.data(self.field_model.index(rc, 2, parent), Qt.DisplayRole)
                checked = self.field_model.data(self.field_model.index(rc, 0, parent), Qt.CheckStateRole)
                s.setValue('/plugins/qquake/output_field_{}'.format(path.replace('>', '_')), checked)

        super().accept()

    def reset_fields(self):
        for r in range(self.field_model.rowCount(QModelIndex())):
            parent = self.field_model.index(r, 0, QModelIndex())
            for rc in range(self.field_model.rowCount(parent)):
                self.field_model.setData(self.field_model.index(rc, 0, parent), True, Qt.CheckStateRole)
