# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MenuBuilderDialog
                                 A QGIS plugin
 Create your own menu with shortcuts to layers, projects and so on
                             -------------------
        begin                : 2015-07-23
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Oslandia
        email                : ludovic dot delaune@oslandia dot com
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
from __future__ import unicode_literals
import os

from PyQt4.QtCore import (
    Qt, QSettings, QObject, SIGNAL, pyqtSlot, QAbstractItemModel, QRect
)
from PyQt4.QtGui import (
    QMessageBox, QDialog, QAbstractItemView,
    QStandardItem, QStandardItemModel, QTreeView
)
from PyQt4 import uic
from qgis.core import QgsBrowserModel, QgsDataSourceURI, QgsCredentials
from qgis.core import QgsMimeDataUtils


import psycopg2

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'menu_builder_dialog_base.ui'))


class MenuBuilderDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor"""
        super(MenuBuilderDialog, self).__init__(parent)

        self.setupUi(self)

        # add list of defined postgres connections
        settings = QSettings()
        settings.beginGroup("/PostgreSQL/connections")
        keys = settings.childGroups()
        self.combo_database.addItems(keys)
        settings.endGroup()

        # connect to database when it has been selected
        QObject.connect(
            self.combo_database,
            SIGNAL("activated(int)"),
            self.set_connection
        )

        self.browser = QgsBrowserModel()

        QObject.connect(
            self.source,
            SIGNAL("clicked(QModelIndex)"),
            self.debug_source
        )

        self.target = CustomQtTreeView(self)
        self.target.setGeometry(QRect(440, 150, 371, 451))
        self.target.setAcceptDrops(True)
        self.target.setDragDropMode(QAbstractItemView.DragDrop)
        self.target.setObjectName("target")

        self.source.setModel(self.browser)
        self.source.setDragEnabled(True)
        self.source.setHeaderHidden(True)
        self.source.setAcceptDrops(False)
        self.source.setDropIndicatorShown(True)

        self.menu = MyModel()
        self.menu.setHorizontalHeaderLabels(["Menus"])
        self.menu.setItem(0, QStandardItem('Menu1'))
        self.menu.setItem(1, QStandardItem('Menu2'))
        self.target.setModel(self.menu)
        self.target.setAnimated(True)

        self.profile_list = []

    @pyqtSlot("QModelIndex")
    def debug_source(self, index):
        if not self.browser.hasChildren(index):
            data = self.browser.mimeData([index])
            uri = QgsMimeDataUtils.decodeUriList(data)[0].uri
            print uri

    def update_profiles(self):
        """
        update profile list
        """
        cur = self.connection.cursor()
        cur.execute("select tablename from pg_tables where schemaname = 'public'")
        tables = cur.fetchall()
        self.combo_profile.clear()
        self.combo_profile.addItems([row[0] for row in tables])

    def set_connection(self):
        selected = self.combo_database.currentText()
        settings = QSettings()
        settings.beginGroup("/PostgreSQL/connections/{}".format(selected))

        if not settings.contains("database"):
            # no entry?
            QMessageBox.critical(self, "Error", "There is no defined database connection")
            return

        uri = QgsDataSourceURI()

        settingsList = ["service", "host", "port", "database", "username", "password"]
        service, host, port, database, username, password = map(lambda x: settings.value(x, "", type=str), settingsList)

        useEstimatedMetadata = settings.value("estimatedMetadata", False, type=bool)
        sslmode = settings.value("sslmode", QgsDataSourceURI.SSLprefer, type=int)

        settings.endGroup()

        if service:
            uri.setConnection(service, database, username, password, sslmode)
        else:
            uri.setConnection(host, port, database, username, password, sslmode)

        uri.setUseEstimatedMetadata(useEstimatedMetadata)

        # try:
        self.connect_to_uri(uri)
        self.update_profiles()

    def connect_to_uri(self, uri):
        self.host = uri.host() or os.environ.get('PGHOST')
        self.port = uri.port() or os.environ.get('PGPORT')

        username = uri.username() or os.environ.get('PGUSER') or os.environ.get('USER')
        password = uri.password() or os.environ.get('PGPASSWORD')

        try:
            self.connection = psycopg2.connect(uri.connectionInfo())
        except self.connection_error_types(), e:
            err = str(e)
            conninfo = uri.connectionInfo()

            (ok, username, password) = QgsCredentials.instance().get(conninfo, username, password, err)
            if not ok:
                raise Exception(e)

            if username:
                uri.setUsername(username)

            if password:
                uri.setPassword(password)

            try:
                self.connection = psycopg2.connect(uri.connectionInfo())
            except self.connection_error_types(), e:
                raise Exception(e)

        return True

    def connection_error_types(self):
        return psycopg2.InterfaceError, psycopg2.OperationalError

    def create_table(self):
        """
        Creates the metadata table in public schema
        """
        pass


class CustomQtTreeView(QTreeView):
    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()


class MyModel(QStandardItemModel):
    def dropMimeData(self, mimedata, action, row, column, parentIndex):
        """
        Handles the dropping of an item onto the model.
        De-serializes the data into a TreeItem instance and inserts it into the model.
        """
        # if not mimedata.hasFormat( 'application/x-pynode-item-instance' ):
        # return False
        data = QgsMimeDataUtils.decodeUriList(mimedata)[0]
        print 'name', data.name
        print 'data', data.data
        print 'uri', data.uri
        item = QStandardItem(data.name)
        item.setData([mimedata])
        dropParent = self.itemFromIndex(parentIndex)
        dropParent.appendRow(item)
        dropParent.emitDataChanged()
        return True

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)

        if index.isValid():
            return Qt.ItemIsEditable | Qt.ItemIsDragEnabled | \
                    Qt.ItemIsDropEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags
