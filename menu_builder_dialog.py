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
import json
import pickle

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

        QObject.connect(
            self.combo_profile,
            SIGNAL("activated(int)"),
            self.load_profile
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
        self.table = 'qgis_menubuilder_metadata'

    def add_menu(self):
        item = QStandardItem('NewMenu')
        item.setIcon(QIcon(':/plugins/MenuBuilder/resources/menu.svg'))
        # select current index selected and insert as a sibling
        brother = self.target.selectedIndexes()

        if not brother or not brother[0].parent():
            # no selection, add menu at the top level
            self.menu.insertRow(self.menu.rowCount(), item)
            return

        parent = self.menu.itemFromIndex(brother[0].parent())
        if not parent:
            self.menu.insertRow(self.menu.rowCount(), item)
            return
        parent.appendRow(item)

    def set_connection(self):
        selected = self.combo_database.currentText()
        if not selected:
            return
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
        except self.pg_error_types() as e:
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

            self.connection = psycopg2.connect(uri.connectionInfo())

        return True

    def pg_error_types(self):
        return psycopg2.InterfaceError, psycopg2.OperationalError

    def update_profiles(self):
        """
        update profile list
        """
        cur = self.connection.cursor()
        cur.execute("""
            select 1
            from pg_tables
                where schemaname = 'public'
                and tablename = '{}'
            """.format(self.table))
        tables = cur.fetchone()
        if not tables:
            box = QMessageBox(
                QMessageBox.Warning,
                "Menu Builder",
                self.tr("Table 'public.{}' not found in this database, "
                        "would you like to create it now ?".format(self.table)),
                QMessageBox.Cancel | QMessageBox.Yes,
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
                    """.format(self.table))
                self.connection.commit()
                return False

        cur.execute("""
            select distinct(profile) from {}
            """.format(self.table))
        profiles = [row[0] for row in cur.fetchall()]
        self.combo_profile.clear()
        self.combo_profile.addItems(profiles)
        self.load_profile(self.combo_profile.currentIndex())

    def load_profile(self, current_index):
        profile_name = self.combo_profile.itemText(current_index)
        if not getattr(self, 'connection', False):
            QMessageBox(
                QMessageBox.Warning,
                "Menu Builder",
                self.tr("Not connected to any database, please select one"),
                QMessageBox.Ok,
                self
            ).exec_()
            return

        cur = self.connection.cursor()
        try:
            cur.execute("""
                select name, profile, model_index, datasource_uri
                from {}
                where profile = '{}'
                order by id
                """.format(self.table, profile_name))
            rows = cur.fetchall()
            self.menu.clear()
            for row in rows:
                parent = self.menu.invisibleRootItem()
                for idx, name in json.loads(row[2]):
                    # add menus
                    item = QStandardItem(name)
                    item.setData(row[3])
                    parent.appendRow(item)
                    parent = item
                # print 'name', row[0], 'profile', row[1], 'model_index', json.loads(row[2]), row[3]

        except self.pg_error_types() as e:
            self.connection.rollback()
            raise e

    def save_changes(self):
        """
        Save changes in the postgres table
        """
        if not getattr(self, 'connection', False):
            QMessageBox(
                QMessageBox.Warning,
                "Menu Builder",
                self.tr("Please select database and profile before saving !"),
                QMessageBox.Ok,
                self
            ).exec_()
            return
        cur = self.connection.cursor()
        try:
            cur.execute("delete from {} where profile = '{}'".format(
                self.table, self.combo_profile.currentText()))
            for item, uri in self.target.iteritems():
                cur.execute("""
                insert into {} (name,profile,model_index,datasource_uri)
                values ('{}', '{}', '{}', {})
                """.format(
                    self.table,
                    item[-1][1],
                    self.combo_profile.currentText(),
                    json.dumps(item),
                    psycopg2.Binary(uri.encode('utf-8'))
                ))
        except psycopg2.ProgrammingError as e:
            self.connection.rollback()
            raise e

        self.connection.commit()
        return True

    def accept(self):
        if self.save_changes():
            QDialog.reject(self)


class CustomQtTreeView(QTreeView):
    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragEnterEvent(self, event):
        # refuse if it's not a qgis mimetype
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

    def iteritems(self, level=0):
        """
        Dump model to store in database.
        Generates each level recursively
        """
        rowcount = self.model().rowCount()
        for itemidx in range(rowcount):
            # iterate over parents
            parent = self.model().itemFromIndex(self.model().index(itemidx, 0))
            for item, uri in self.traverse_tree(parent, []):
                yield item, uri

    def traverse_tree(self, parent, identifier):
        """
        Iterate over childs, recursively
        """
        identifier.append([parent.row(), parent.text()])
        for row in range(parent.rowCount()):
            child = parent.child(row)
            if child.hasChildren():
                # child is a menu ?
                for item in self.traverse_tree(child, identifier):
                    yield item
            else:
                # add leaf
                sibling = list(identifier)
                sibling.append([child.row(), child.text()])
                yield sibling, child.data().uri


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
