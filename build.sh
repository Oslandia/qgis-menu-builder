#!/bin/sh
pyuic5 menu_builder_dialog_base.ui -o menu_builder_dialog_base.py
pyrcc5 -o resources.py resources.qrc
