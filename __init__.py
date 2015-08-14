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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load MenuBuilder class from file MenuBuilder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .menu_builder import MenuBuilder
    return MenuBuilder(iface)
