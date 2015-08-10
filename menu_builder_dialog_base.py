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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(810, 617)
        Dialog.setSizeGripEnabled(True)
        Dialog.setModal(True)
        self.verticalLayout_3 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.source = QtGui.QTreeView(Dialog)
        self.source.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.source.sizePolicy().hasHeightForWidth())
        self.source.setSizePolicy(sizePolicy)
        self.source.setAutoFillBackground(True)
        self.source.setObjectName(_fromUtf8("source"))
        self.source.header().setVisible(True)
        self.horizontalLayout.addWidget(self.source)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setVerticalSpacing(6)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.button_add_menu = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_add_menu.sizePolicy().hasHeightForWidth())
        self.button_add_menu.setSizePolicy(sizePolicy)
        self.button_add_menu.setObjectName(_fromUtf8("button_add_menu"))
        self.gridLayout.addWidget(self.button_add_menu, 6, 0, 1, 1)
        self.label_database = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_database.sizePolicy().hasHeightForWidth())
        self.label_database.setSizePolicy(sizePolicy)
        self.label_database.setObjectName(_fromUtf8("label_database"))
        self.gridLayout.addWidget(self.label_database, 1, 0, 1, 1)
        self.combo_database = QtGui.QComboBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combo_database.sizePolicy().hasHeightForWidth())
        self.combo_database.setSizePolicy(sizePolicy)
        self.combo_database.setEditable(False)
        self.combo_database.setObjectName(_fromUtf8("combo_database"))
        self.gridLayout.addWidget(self.combo_database, 2, 0, 1, 1)
        self.combo_profile = QtGui.QComboBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combo_profile.sizePolicy().hasHeightForWidth())
        self.combo_profile.setSizePolicy(sizePolicy)
        self.combo_profile.setEditable(True)
        self.combo_profile.setObjectName(_fromUtf8("combo_profile"))
        self.gridLayout.addWidget(self.combo_profile, 5, 0, 1, 1)
        self.label_profile = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_profile.sizePolicy().hasHeightForWidth())
        self.label_profile.setSizePolicy(sizePolicy)
        self.label_profile.setObjectName(_fromUtf8("label_profile"))
        self.gridLayout.addWidget(self.label_profile, 3, 0, 1, 1)
        self.button_delete_profile = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_delete_profile.sizePolicy().hasHeightForWidth())
        self.button_delete_profile.setSizePolicy(sizePolicy)
        self.button_delete_profile.setText(_fromUtf8(""))
        self.button_delete_profile.setObjectName(_fromUtf8("button_delete_profile"))
        self.gridLayout.addWidget(self.button_delete_profile, 5, 1, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.button_delete_profile.raise_()

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Menu Configuration", None))
        self.button_add_menu.setText(_translate("Dialog", "Add a menu", None))
        self.label_database.setText(_translate("Dialog", "Choose database where profiles are stored", None))
        self.label_profile.setText(_translate("Dialog", "Choose profile", None))
        self.button_delete_profile.setToolTip(_translate("Dialog", "Delete current profile", None))

