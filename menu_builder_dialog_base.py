# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'menu_builder_dialog_base.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MenuBuilderDialogBase(object):
    def setupUi(self, MenuBuilderDialogBase):
        MenuBuilderDialogBase.setObjectName(_fromUtf8("MenuBuilderDialogBase"))
        MenuBuilderDialogBase.resize(844, 649)
        self.button_box = QtGui.QDialogButtonBox(MenuBuilderDialogBase)
        self.button_box.setGeometry(QtCore.QRect(630, 610, 181, 32))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.combo_database = QtGui.QComboBox(MenuBuilderDialogBase)
        self.combo_database.setGeometry(QtCore.QRect(40, 40, 261, 31))
        self.combo_database.setEditable(False)
        self.combo_database.setObjectName(_fromUtf8("combo_database"))
        self.label_database = QtGui.QLabel(MenuBuilderDialogBase)
        self.label_database.setGeometry(QtCore.QRect(40, 20, 391, 16))
        self.label_database.setObjectName(_fromUtf8("label_database"))
        self.source = QtGui.QTreeView(MenuBuilderDialogBase)
        self.source.setGeometry(QtCore.QRect(40, 150, 371, 451))
        self.source.setAutoFillBackground(True)
        self.source.setObjectName(_fromUtf8("source"))
        self.source.header().setVisible(True)
        self.combo_profile = QtGui.QComboBox(MenuBuilderDialogBase)
        self.combo_profile.setGeometry(QtCore.QRect(40, 100, 261, 31))
        self.combo_profile.setEditable(True)
        self.combo_profile.setObjectName(_fromUtf8("combo_profile"))
        self.label_profile = QtGui.QLabel(MenuBuilderDialogBase)
        self.label_profile.setGeometry(QtCore.QRect(40, 80, 151, 16))
        self.label_profile.setObjectName(_fromUtf8("label_profile"))
        self.button_add_menu = QtGui.QPushButton(MenuBuilderDialogBase)
        self.button_add_menu.setGeometry(QtCore.QRect(440, 100, 31, 31))
        self.button_add_menu.setText(_fromUtf8(""))
        self.button_add_menu.setObjectName(_fromUtf8("button_add_menu"))
        self.label_add_menu = QtGui.QLabel(MenuBuilderDialogBase)
        self.label_add_menu.setGeometry(QtCore.QRect(480, 108, 161, 16))
        self.label_add_menu.setObjectName(_fromUtf8("label_add_menu"))

        self.retranslateUi(MenuBuilderDialogBase)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("accepted()")), MenuBuilderDialogBase.accept)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("rejected()")), MenuBuilderDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(MenuBuilderDialogBase)

    def retranslateUi(self, MenuBuilderDialogBase):
        MenuBuilderDialogBase.setWindowTitle(_translate("MenuBuilderDialogBase", "Menu Builder", None))
        self.label_database.setText(_translate("MenuBuilderDialogBase", "Choose database where profiles are stored", None))
        self.label_profile.setText(_translate("MenuBuilderDialogBase", "Choose profile", None))
        self.label_add_menu.setText(_translate("MenuBuilderDialogBase", "Add a menu", None))

