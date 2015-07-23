# -*- coding: utf-8 -*-
from qgis.core import QgsMapLayerRegistry

class action():
  def __init__(self, iface):
    # Fermer toutes les couches d'un coup :
    for L in iface.legendInterface().layers():
      QgsMapLayerRegistry.instance().removeMapLayer(L.id())
