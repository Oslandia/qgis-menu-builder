# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MenuBuilder
                                 A QGIS plugin
 Create your own menu with shortcuts to layers, projects and so on
                             -------------------
        begin                : 2015-07-23
        copyright            : (C) 2015 by Oslandia
        email                : ludovic dot delaune@oslandia dot com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load MenuBuilder class from file MenuBuilder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .menu_builder import MenuBuilder
    return MenuBuilder(iface)
