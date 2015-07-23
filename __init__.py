#!python
# -*- coding: utf_8 -*-
"""
/***************************************************************************
 Plugin Créer ses propres menus
 Date : 2013-07-22
 ***************************************************************************/
 /***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
def classFactory(iface): 
  from Menus import Menus
  return Menus(iface)
