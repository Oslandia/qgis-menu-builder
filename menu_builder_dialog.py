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
from collections import defaultdict
import os

import psycopg2
from PyQt4.QtCore import (
    Qt, QSettings, QObject, SIGNAL,
    QAbstractItemModel, QRect
)
from PyQt4.QtGui import (
    QIcon, QMessageBox, QDialog, QStandardItem,
    QStandardItemModel, QTreeView, QAbstractItemView
)
from PyQt4 import uic
from qgis.core import QgsBrowserModel, QgsDataSourceURI, QgsCredentials
from qgis.core import QgsMimeDataUtils


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'menu_builder_dialog_base.ui'))

QGIS_MIMETYPE = 'application/x-vnd.qgis.qgis.uri'


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

        self.button_add_menu.setIcon(QIcon(":/plugins/MenuBuilder/resources/plus.svg"))

        # connect to database when it has been selected
        QObject.connect(
            self.combo_database,
            SIGNAL("activated(int)"),
            self.set_connection
        )

        self.browser = QgsBrowserModel()

        QObject.connect(
            self.button_add_menu,
            SIGNAL("released()"),
            self.add_menu
        )

        self.target = CustomQtTreeView(self)
        self.target.setGeometry(QRect(440, 150, 371, 451))
        self.target.setAcceptDrops(True)
        self.target.setDragEnabled(True)
        self.target.setDragDropMode(QAbstractItemView.DragDrop)
        self.target.setObjectName("target")
        self.target.setDropIndicatorShown(True)
        self.target.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.source.setModel(self.browser)
        self.source.setHeaderHidden(True)
        self.source.setAcceptDrops(False)
        self.source.setDragEnabled(True)
        self.source.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.menu = MenuTreeModel(self)
        self.menu.setHorizontalHeaderLabels(["Menus"])
        self.target.setModel(self.menu)
        self.target.setAnimated(True)

        self.profile_list = []

    def add_menu(self):
        item = QStandardItem('NewMenu')
        item.setIcon(QIcon(':/plugins/MenuBuilder/resources/menu.svg'))
        self.menu.insertRow(self.menu.rowCount(), item)

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
        service, host, port, database, username, password = map(
            lambda x: settings.value(x, "", type=str), settingsList)

        useEstimatedMetadata = settings.value("estimatedMetadata", False, type=bool)
        sslmode = settings.value("sslmode", QgsDataSourceURI.SSLprefer, type=int)

        settings.endGroup()

        if service:
            uri.setConnection(service, database, username, password, sslmode)
        else:
            uri.setConnection(host, port, database, username, password, sslmode)

        uri.setUseEstimatedMetadata(useEstimatedMetadata)

        # connect to db and update profile list
        self.connect_to_uri(uri)
        self.update_profiles()

    def connect_to_uri(self, uri):
        self.host = uri.host() or os.environ.get('PGHOST')
        self.port = uri.port() or os.environ.get('PGPORT')

        username = uri.username() or os.environ.get('PGUSER') or os.environ.get('USER')
        password = uri.password() or os.environ.get('PGPASSWORD')

        try:
            self.connection = psycopg2.connect(uri.connectionInfo())
        except self.connection_error_types() as e:
            err = str(e)
            conninfo = uri.connectionInfo()

            ok, username, password = QgsCredentials.instance().get(
                conninfo, username, password, err)
            if not ok:
                raise Exception(e)

            if username:
                uri.setUsername(username)

            if password:
                uri.setPassword(password)

            try:
                self.connection = psycopg2.connect(uri.connectionInfo())
            except self.connection_error_types() as e:
                raise Exception(e)

        return True

    def connection_error_types(self):
        return psycopg2.InterfaceError, psycopg2.OperationalError

    def update_profiles(self):
        """
        update profile list
        """
        table = 'qgis_menubuilder_metadata'

        cur = self.connection.cursor()
        cur.execute("""
            select 1
            from pg_tables
                where schemaname = 'public'
                and tablename = '{}'
            """.format(table))
        tables = cur.fetchone()
        if not tables:
            box = QMessageBox(
                QMessageBox.Warning,
                "Menu Builder",
                self.tr("Table 'public.{}' not found in this database, "
                        "would you like to create it now ?".format(table)),
                QMessageBox.Cancel | QMessageBox.Yes | QMessageBox.Close,
                self
            )
            ret = box.exec_()
            if ret == QMessageBox.Cancel:
                return False
            elif ret == QMessageBox.Yes:
                cur.execute("""
                    create table {} (
                        id serial,
                        name varchar,
                        profile varchar,
                        model_index varchar,
                        datasource_uri bytea
                    )
                    """.format(table))
                self.connection.commit()
                return False

        cur.execute("""
            select distinct(profile) from {}
            """.format(table))
        profiles = [row[0] for row in cur.fetchall()]
        self.combo_profile.clear()
        self.combo_profile.addItems(profiles)

    def create_table(self):
        """
        Creates the metadata table in public schema
        """
        raise NotImplementedError()

    def save_changes(self):
        """
        Save changes in the postgres table
        """
        raise NotImplementedError()

    def accept(self):
        if self.save_changes():
            QDialog.reject(self)


class CustomQtTreeView(QTreeView):
    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragEnterEvent(self, event):
        # refuse if it's not a qgis mimetype
        print 'entering drag'
        print [not idx.parent() for idx in self.selectedIndexes()]
        if any([not idx.parent() for idx in self.selectedIndexes()]):
            return False
        if event.mimeData().hasFormat(QGIS_MIMETYPE):
            event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.dropItem()

    def dropItem(self):
        model = self.selectionModel().model()
        parents = defaultdict(list)
        for idx in self.selectedIndexes():
            parents[idx.parent()].append(idx)

        for parent, idx_list in parents.items():
            for diff, index in enumerate(idx_list):
                model.removeRow(index.row() - diff, parent)


class MenuTreeModel(QStandardItemModel):
    def dropMimeData(self, mimedata, action, row, column, parentIndex):
        """
        Handles the dropping of an item onto the model.
        De-serializes the data and inserts it into the model.
        """
        # decode data using qgis helpers
        uri_list = QgsMimeDataUtils.decodeUriList(mimedata)
        if not uri_list:
            return False
        # find parent item
        dropParent = self.itemFromIndex(parentIndex)
        if not dropParent:
            return False
        # each uri will become a new item
        for uri in uri_list:
            item = QStandardItem(uri.name)
            item.setData(uri)
            dropParent.appendRow(item)
        dropParent.emitDataChanged()

        return True

    def mimeData(self, indexes):
        """
        Used to serialize data
        """
        if not indexes:
            return 0
        items = [self.itemFromIndex(idx) for idx in indexes]
        if not items:
            return 0
        # reencode items
        mimedata = QgsMimeDataUtils.encodeUriList([item.data() for item in items])
        return mimedata

    def mimeTypes(self):
        return [QGIS_MIMETYPE]

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)

        if index.isValid():
            return Qt.ItemIsEditable | Qt.ItemIsDragEnabled | \
                    Qt.ItemIsDropEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction
