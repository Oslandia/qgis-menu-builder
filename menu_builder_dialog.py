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
import re
import json
from contextlib import contextmanager
from collections import defaultdict
from functools import wraps, partial

import psycopg2

from PyQt4.QtCore import Qt, QSettings, QObject, SIGNAL, QRect, QMimeData
from PyQt4.QtGui import (
    QIcon, QMessageBox, QDialog, QStandardItem, QMenu, QAction,
    QStandardItemModel, QTreeView, QAbstractItemView,
    QDockWidget, QWidget, QVBoxLayout, QSizePolicy,
    QSortFilterProxyModel, QLineEdit
)
from PyQt4 import uic
from qgis.core import (
    QgsMapLayerRegistry, QgsBrowserModel, QgsDataSourceURI,
    QgsCredentials, QgsVectorLayer, QgsMimeDataUtils, QgsRasterLayer
)


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'menu_builder_dialog_base.ui'))

QGIS_MIMETYPE = 'application/x-vnd.qgis.qgis.uri'


ICON_MAPPER = {
    'postgres': ":/plugins/MenuBuilder/resources/postgis.svg",
    'WMS': ":/plugins/MenuBuilder/resources/wms.svg",
    'WFS': ":/plugins/MenuBuilder/resources/wfs.svg",
    'OWS': ":/plugins/MenuBuilder/resources/ows.svg",
    'spatialite': ":/plugins/MenuBuilder/resources/spatialite.svg",
    'mssql': ":/plugins/MenuBuilder/resources/mssql.svg",
    'gdal': ":/plugins/MenuBuilder/resources/gdal.svg",
    'ogr': ":/plugins/MenuBuilder/resources/ogr.svg",
}


class MenuBuilderDialog(QDialog, FORM_CLASS):
    def __init__(self, uiparent):
        """Constructor"""
        super(MenuBuilderDialog, self).__init__()

        self.setupUi(self)

        # reference to caller
        self.uiparent = uiparent

        # add list of defined postgres connections
        settings = QSettings()
        settings.beginGroup("/PostgreSQL/connections")
        keys = settings.childGroups()
        self.combo_database.addItems(keys)
        self.combo_database.setCurrentIndex(-1)
        self.combo_profile.setCurrentIndex(-1)
        settings.endGroup()

        # add custom icons
        self.button_add_menu.setIcon(QIcon(":/plugins/MenuBuilder/resources/plus.svg"))
        self.button_delete_profile.setIcon(QIcon(":/plugins/MenuBuilder/resources/delete.svg"))

        # custom qtreeview
        self.target = CustomQtTreeView(self)
        self.target.setGeometry(QRect(440, 150, 371, 451))
        self.target.setAcceptDrops(True)
        self.target.setDragEnabled(True)
        self.target.setDragDropMode(QAbstractItemView.DragDrop)
        self.target.setObjectName("target")
        self.target.setDropIndicatorShown(True)
        self.target.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.target.setHeaderHidden(True)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.target.sizePolicy().hasHeightForWidth())
        self.target.setSizePolicy(sizePolicy)
        self.target.setAutoFillBackground(True)
        self.verticalLayout_2.addWidget(self.target)

        self.browser = QgsBrowserModel()
        self.source.setModel(self.browser)
        self.source.setHeaderHidden(True)
        self.source.setDragEnabled(True)
        self.source.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.menu = MenuTreeModel(self)
        self.target.setModel(self.menu)
        self.target.setAnimated(True)

        # add a dock widget
        self.dock_widget = QDockWidget("Menus", self.uiparent.iface.mainWindow())
        self.dock_widget.resize(400, 300)
        self.dock_widget.setFloating(True)
        self.dock_widget.setObjectName(self.tr("Menu Tree"))
        self.dock_widget_content = QWidget()
        self.dock_widget.setWidget(self.dock_widget_content)
        dock_layout = QVBoxLayout()
        self.dock_widget_content.setLayout(dock_layout)
        self.dock_view = DockQtTreeView(self.dock_widget_content)
        self.dock_view.setDragDropMode(QAbstractItemView.DragOnly)
        self.dock_menu_filter = QLineEdit()
        self.dock_menu_filter.setPlaceholderText(self.tr("Filter on comments (postgis only)"))
        dock_layout.addWidget(self.dock_menu_filter)
        dock_layout.addWidget(self.dock_view)
        self.dock_view.setHeaderHidden(True)
        self.dock_view.setDragEnabled(True)
        self.dock_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dock_view.setAnimated(True)
        self.dock_view.setObjectName("treeView")
        self.proxy_model = LeafFilterProxyModel(self)
        self.proxy_model.setFilterRole(Qt.ToolTipRole)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.profile_list = []
        self.table = 'qgis_menubuilder_metadata'

        self.layer_handler = {
            'vector': self.load_vector,
            'raster': self.load_raster
        }

        # connect signals and handlers
        QObject.connect(self.combo_database, SIGNAL("activated(int)"), self.set_connection)
        QObject.connect(self.combo_profile, SIGNAL("activated(int)"), partial(self.load_menu4profile, self.menu))
        QObject.connect(self.button_add_menu, SIGNAL("released()"), self.add_menu)
        QObject.connect(self.button_delete_profile, SIGNAL("released()"), self.del_profile)
        QObject.connect(self.dock_menu_filter, SIGNAL("cursorPositionChanged(int, int)"), self.filter_update)

    def filter_update(self, old, new):
        text = self.dock_menu_filter.displayText()
        self.proxy_model.setFilterRegExp(text)

    def show_dock(self):
        state = self.activate_dock.isChecked()
        if not state:
            # just hide widget
            self.dock_widget.setVisible(state)
            return
        # dock must be read only and deepcopy of model is not supported (c++ inside!)
        menu = MenuTreeModel(self)
        self.load_menu4profile(menu, self.combo_profile.currentIndex())
        menu.setHorizontalHeaderLabels(["Menus"])
        self.dock_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.proxy_model.setSourceModel(menu)
        self.dock_view.setModel(self.proxy_model)

        self.dock_widget.setVisible(state)

    def show_menus(self):
        state = self.activate_menubar.isChecked()
        if state:
            self.load_menus()
            return
        # remove menus
        for menu in self.uiparent.menus:
            self.uiparent.iface.mainWindow().menuBar().removeAction(menu.menuAction())

    def add_menu(self):
        """
        Add a menu inside qtreeview
        """
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
        self.update_profile_list()

    @contextmanager
    def transaction(self):
        try:
            yield
            self.connection.commit()
        except self.pg_error_types() as e:
            self.connection.rollback()
            raise e

    def check_connected(func):
        """
        Decorator that checks if a database connection is active before executing function
        """
        @wraps(func)
        def wrapped(inst, *args, **kwargs):
            if not getattr(inst, 'connection', False):
                QMessageBox(
                    QMessageBox.Warning,
                    "Menu Builder",
                    inst.tr("Not connected to any database, please select one"),
                    QMessageBox.Ok,
                    inst
                ).exec_()
                return
            if inst.connection.closed:
                QMessageBox(
                    QMessageBox.Warning,
                    "Menu Builder",
                    inst.tr("Not connected to any database, please select one"),
                    QMessageBox.Ok,
                    inst
                ).exec_()
                return
            return func(inst, *args, **kwargs)
        return wrapped

    def connect_to_uri(self, uri):
        self.close_connection()
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

    def update_profile_list(self):
        """
        update profile list
        """
        with self.transaction():
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
            saved_profile = self.combo_profile.currentText()
            self.combo_profile.clear()
            self.combo_profile.addItems(profiles)
            self.combo_profile.setCurrentIndex(self.combo_profile.findText(saved_profile))

    @check_connected
    def del_profile(self):
        """
        Delete profile currently selected
        """
        idx = self.combo_profile.currentIndex()
        profile = self.combo_profile.itemText(idx)
        box = QMessageBox(
            QMessageBox.Warning,
            "Menu Builder",
            self.tr("Delete '{}' profile ?".format(profile)),
            QMessageBox.Cancel | QMessageBox.Yes,
            self
        )
        ret = box.exec_()
        if ret == QMessageBox.Cancel:
            return False
        elif ret == QMessageBox.Yes:
            self.combo_profile.removeItem(idx)
            with self.transaction():
                cur = self.connection.cursor()
                cur.execute("""
                    delete from {}
                    where profile = '{}'
                    """.format(self.table, profile))

    @check_connected
    def load_menu4profile(self, model, current_index):
        profile_name = self.combo_profile.itemText(current_index)

        menudict = {}

        with self.transaction():
            cur = self.connection.cursor()
            select = """
                SET bytea_output TO escape;
                select name, profile, model_index, datasource_uri
                from {}
                where profile = '{}'
                """.format(self.table, profile_name)
            cur.execute(select)
            rows = cur.fetchall()
            model.clear()
            for name, profile, model_index, datasource_uri in rows:
                menu = model.invisibleRootItem()
                indexes = json.loads(model_index)
                parent = '{}-{}/'.format(indexes[0][0], indexes[0][1])
                for idx, subname in indexes[:-1]:
                    parent += '{}-{}/'.format(idx, subname)
                    if parent in menudict:
                        # already created entry
                        menu = menudict[parent]
                        continue
                    # create menu
                    item = QStandardItem(subname)
                    qmimedata = QMimeData()
                    qmimedata.setData(QGIS_MIMETYPE, str(datasource_uri))
                    uri_struct = QgsMimeDataUtils.decodeUriList(qmimedata)[0]
                    item.setData(uri_struct)
                    item.setIcon(QIcon(':/plugins/MenuBuilder/resources/menu.svg'))
                    menu.appendRow(item)
                    menudict[parent] = item

                # add leaf (layer item)
                item = QStandardItem(name)
                qmimedata = QMimeData()
                qmimedata.setData(QGIS_MIMETYPE, str(datasource_uri))
                uri_struct = QgsMimeDataUtils.decodeUriList(qmimedata)[0]
                if uri_struct.providerKey in ICON_MAPPER:
                    item.setIcon(QIcon(ICON_MAPPER[uri_struct.providerKey]))
                item.setData(uri_struct)
                if uri_struct.providerKey == 'postgres':
                    # set What's This to postgres comment
                    comment = self.get_table_comment(uri_struct.uri)
                    item.setWhatsThis(comment)
                    item.setToolTip(comment)
                menudict[parent].appendRow(item)

    @check_connected
    def save_changes(self):
        """
        Save changes in the postgres table
        """
        if not self.combo_profile.currentText():
            QMessageBox(
                QMessageBox.Warning,
                "Menu Builder",
                self.tr("Profile cannot be empty"),
                QMessageBox.Ok,
                self
            ).exec_()
            return False

        with self.transaction():
            cur = self.connection.cursor()
            cur.execute("delete from {} where profile = '{}'".format(
                self.table, self.combo_profile.currentText()))
            for item, data in self.target.iteritems():
                if not data:
                    continue
                qmimedata = QgsMimeDataUtils.encodeUriList([data]).data(QGIS_MIMETYPE)
                cur.execute("""
                insert into {} (name,profile,model_index,datasource_uri)
                values ('{}', '{}', '{}', {})
                """.format(
                    self.table,
                    item[-1][1],
                    self.combo_profile.currentText(),
                    json.dumps(item),
                    psycopg2.Binary(str(qmimedata))
                ))

        self.update_profile_list()
        self.show_dock()
        self.show_menus()
        return True

    @check_connected
    def load_menus(self):
        """
        Load menus in the main windows qgis bar
        """
        # remove previous menus
        for menu in self.uiparent.menus:
            self.uiparent.iface.mainWindow().menuBar().removeAction(menu.menuAction())

        with self.transaction():
            cur = self.connection.cursor()
            select = """
                SET bytea_output TO escape;
                select name, model_index, datasource_uri
                from {}
                where profile = '{}'
                """.format(self.table, self.combo_profile.currentText())
            cur.execute(select)
            rows = cur.fetchall()
        # item accessor ex: '0-menu/0-submenu/1-item/'
        menudict = {}
        # reference to parent item
        parent = ''
        # reference to qgis main menu bar
        menubar = self.uiparent.iface.mainWindow().menuBar()

        for name, model_index, datasource_uri in rows:
            qmimedata = QMimeData()
            qmimedata.setData(QGIS_MIMETYPE, str(datasource_uri))
            uri_struct = QgsMimeDataUtils.decodeUriList(qmimedata)[0]
            indexes = json.loads(model_index)
            # root menu
            parent = '{}-{}/'.format(indexes[0][0], indexes[0][1])
            if parent not in menudict:
                menu = QMenu(self.uiparent.iface.mainWindow())
                self.uiparent.menus.append(menu)
                menu.setObjectName(indexes[0][1])
                menu.setTitle(indexes[0][1])
                menubar.insertMenu(self.uiparent.iface.firstRightStandardMenu().menuAction(), menu)
                menudict[parent] = menu
            else:
                # menu already there
                menu = menudict[parent]

            for idx, subname in indexes[1:-1]:
                # intermediate submenus
                parent += '{}-{}/'.format(idx, subname)
                if parent not in menudict:
                    submenu = menu.addMenu(subname)
                    submenu.setObjectName(subname)
                    submenu.setTitle(subname)
                    menu = submenu
                    # store it for later use
                    menudict[parent] = menu
                    continue
                # already treated
                menu = menudict[parent]

            # last item = layer
            layer = QAction(name, self.uiparent.iface.mainWindow())
            if uri_struct.providerKey in ICON_MAPPER:
                layer.setIcon(QIcon(ICON_MAPPER[uri_struct.providerKey]))
            if uri_struct.providerKey == 'postgres':
                # set tooltip to postgres comment
                comment = self.get_table_comment(uri_struct.uri)
                layer.setStatusTip(comment)
                layer.setToolTip(comment)

            layer.setData(uri_struct.uri)
            layer.setWhatsThis(uri_struct.providerKey)
            layer.triggered.connect(self.layer_handler[uri_struct.layerType])
            menu.addAction(layer)

    def get_table_comment(self, uri):
        schema, table = re.match(
            '.*table=(.*)\(.*',
            uri
        ).group(1).strip().replace('"', '').split('.')
        with self.transaction():
            cur = self.connection.cursor()
            select = """
                select description from pg_description
                join pg_class on pg_description.objoid = pg_class.oid
                join pg_namespace on pg_class.relnamespace = pg_namespace.oid
                where relname = '{}' and nspname='{}'
                """.format(table, schema)
            cur.execute(select)
            row = cur.fetchone()
            if row:
                return row[0]
        return ''

    def load_vector(self):
        action = self.sender()
        layer = QgsVectorLayer(
            action.data(),  # uri
            action.text(),  # layer name
            action.whatsThis()  # provider name
        )
        QgsMapLayerRegistry.instance().addMapLayer(layer)

    def load_raster(self):
        action = self.sender()
        layer = QgsRasterLayer(
            action.data(),  # uri
            action.text(),  # layer name
            action.whatsThis()  # provider name
        )
        QgsMapLayerRegistry.instance().addMapLayer(layer)

    def accept(self):
        if self.save_changes():
            QDialog.reject(self)
            self.close_connection()

    def reject(self):
        self.close_connection()
        QDialog.reject(self)

    def close_connection(self):
        """close current pg connection if exists"""
        if getattr(self, 'connection', False):
            if self.connection.closed:
                return
            self.connection.close()


class CustomQtTreeView(QTreeView):
    def __init__(self, *args, **kwargs):
        super(CustomQtTreeView, self).__init__(*args, **kwargs)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragEnterEvent(self, event):
        # refuse if it's not a menu item
        # FIXME
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
                yield sibling, child.data()


class DockQtTreeView(CustomQtTreeView):
    def __init__(self, *args, **kwargs):
        super(DockQtTreeView, self).__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        """override keyevent to avoid deletion of items in the dock"""
        pass


class MenuTreeModel(QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super(MenuTreeModel, self).__init__(*args, **kwargs)

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
            if uri.providerKey in ICON_MAPPER:
                item.setIcon(QIcon(ICON_MAPPER[uri.providerKey]))
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

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction


class LeafFilterProxyModel(QSortFilterProxyModel):
    """
    Class to override the following behaviour:
        If a parent item doesn't match the filter,
        none of its children will be shown.

    This Model matches items which are descendants
    or ascendants of matching items.
    """

    def filterAcceptsRow(self, row_num, source_parent):
        """Overriding the parent function"""

        # Check if the current row matches
        if self.filter_accepts_row_itself(row_num, source_parent):
            return True

        # Traverse up all the way to root and check if any of them match
        if self.filter_accepts_any_parent(source_parent):
            return True

        # Finally, check if any of the children match
        return self.has_accepted_children(row_num, source_parent)

    def filter_accepts_row_itself(self, row_num, parent):
        return super(LeafFilterProxyModel, self).filterAcceptsRow(row_num, parent)

    def filter_accepts_any_parent(self, parent):
        """
        Traverse to the root node and check if any of the
        ancestors match the filter
        """
        while parent.isValid():
            if self.filter_accepts_row_itself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()
        return False

    def has_accepted_children(self, row_num, parent):
        """
        Starting from the current node as root, traverse all
        the descendants and test if any of the children match
        """
        model = self.sourceModel()
        source_index = model.index(row_num, 0, parent)

        children_count = model.rowCount(source_index)
        for i in range(children_count):
            if self.filterAcceptsRow(i, source_index):
                return True
        return False
