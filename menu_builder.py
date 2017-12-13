# -*- coding: utf-8 -*-
"""
MenuBuilder - Create your own menus with your favorite layers

copyright            : (C) 2015 by Oslandia
email                : infos@oslandia.com

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import unicode_literals
from os import path

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from menu_builder_dialog import MenuBuilderDialog
import os.path


def locale_resource(*filepath):
    """
    filepath should be a list of arguments corresponding to the path remaining
    """
    return path.join(path.abspath(path.dirname(__file__)), *filepath)


class MenuBuilder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.plugin_name = self.tr('&Menu Builder')
        # reference to plugin actions
        self.actions = []
        # used to store active menus
        self.menus = []

        # Create the dialog (after translation) and keep reference
        self.dlg = MenuBuilderDialog(self)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MenuBuilder', message)

    def initGui(self):
        """Create the plugin entries inside the QGIS GUI."""
        # create the configure entry
        icon = QIcon(':/plugins/MenuBuilder/resources/settings.svg')
        configure = QAction(icon, self.tr('&Configure Menus'), self.iface.mainWindow())
        configure.triggered.connect(self.run_configure)
        configure.setEnabled(True)
        configure.setStatusTip(self.tr("Configure menus with drag&drop from qgisbrowser"))
        configure.setWhatsThis(self.tr("Configure menus with drag&drop from qgisbrowser"))
        self.iface.addPluginToMenu(self.plugin_name, configure)
        self.actions.append(configure)

        # restore previous session if exists
        try:
            self.dlg.restore_session()
        except Exception as exc:
            QMessageBox(
                QMessageBox.Warning,
                "Restoring MenuBuilder last session",
                exc.message.decode(self.dlg.pgencoding),
                QMessageBox.Ok,
                self.dlg
            ).exec_()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.plugin_name, action)
        for menu in self.menus:
            menu.deleteLater()
        self.iface.removeDockWidget(self.dlg.dock_widget)

    def run_configure(self):
        # show the configure dialog
        self.dlg.show()
        # reload browser content
        self.dlg.browser.reload()
        self.dlg.update_database_list()
        # Run the dialog event loop
        self.dlg.exec_()
