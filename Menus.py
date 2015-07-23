# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtXml, QtWebKit
from qgis.core import QGis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsMapLayerRegistry
from qgis.gui import *  # QgsLayerTreeView #, QgsLayerTreeNode
import imp
import os
from editor.editorGui import xmlEditor

# pour Qgis 2
version = '1.1.1'


class Menus():

    def __init__(self, iface):
        self.iface = iface

    def tr(self, txt, disambiguation=None):
        return QCoreApplication.translate("Menus", txt, disambiguation, QApplication.UnicodeUTF8)

    def initGui(self):
        self.path = os.path.abspath(os.path.dirname(__file__))
        # i18n support
        overrideLocale = QSettings().value("locale/overrideFlag", False)
        localeFullName = QLocale.system().name(
        ) if not overrideLocale else QSettings().value("locale/userLocale", "")
        localePath = self.path + os.sep + "i18n" + os.sep + \
            "menus_" + localeFullName[0:2] + ".qm"  # menus_fr.qm
        # if localeFullName[0:2] == "fr" : reload(sys) ; sys.setdefaultencoding('iso-8859-1')
        # on cherche s'il y a : menus_fr_FR.qm
        if not QFileInfo(localePath).exists():
            localePath = self.path + os.sep + "i18n" + \
                os.sep + "menus_" + localeFullName + ".qm"
        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)
            QCoreApplication.installTranslator(self.translator)

        self.icons = self.path + os.sep + "icons" + os.sep
        # Ajouter un sous-menu dans le menu Extension avec une entrée "Aide" et
        # une pour parametrer
        self.extensionMenuPerso = self.iface.pluginMenu().addMenu(
            QIcon(self.icons + "menus.png"), self.tr("&Create menus"))
        paramAction = QAction(QIcon(
            self.icons + "menus.png"), self.tr("&Set Menus definition file"), self.iface.mainWindow())
        paramAction.setStatusTip(self.tr("Choose Menus definition file"))
        QObject.connect(paramAction, SIGNAL("triggered()"), self.fenetreParam)
        self.extensionMenuPerso.addAction(paramAction)
        aideAction = QAction(
            self.tr("&Help   (version %s)") % version, self.iface.mainWindow())
        aideAction.setStatusTip(self.tr("User guide"))
        QObject.connect(aideAction, SIGNAL("triggered()"), self.fenetreAide)
        self.extensionMenuPerso.addAction(aideAction)

        self.refqm = []  # liste des menus retournées par addMenu( monQmenu )
        self.nbmenus = 0
        self.affichage = self.iface.mainWindow().menuBar()  # le menu Principal

        s = QSettings()
        fichierMenus = s.value("PluginCreerMenus/fileMenus", "")
        if fichierMenus == "":  # 1er demarrage du plugin
            # Menus.xml ira à la base du profil Qgis (ex:
            # USERPROFILE\.qgis2\Menus.xml )
            menusPath = os.path.normpath(self.path + "/../../..") + os.sep
            fichierMenus = menusPath + "Menus.xml"
            # enregistre le param du plugin
            s.setValue("PluginCreerMenus/fileMenus", fichierMenus)
            QFile.copy(self.path + os.sep + "Menus.xml.modele", fichierMenus)
            QFile.copy(
                self.path + os.sep + "ToutFermer.py", menusPath + "ToutFermer.py")
            QFile.copy(self.path + os.sep + "Georef_Organisation administrative (4 couches).qgs",
                       menusPath + "Georef_Organisation administrative (4 couches).qgs")

        else:  # le parametre existe : verifions si le fichier existe
            # cas où Qgis a été déployé avec ce plugin dans un dossier
            # différent
            if not QFile.exists(fichierMenus):
                fichierMenus = os.path.normpath(
                    self.path + "/../../..") + os.sep + "Menus.xml"
                if not QFile.exists(fichierMenus):
                    QFile.copy(
                        self.path + os.sep + "Menus.xml.modele", fichierMenus)
                # enregistre le nouveau param du plugin
                s.setValue("PluginCreerMenus/fileMenus", fichierMenus)

        # chemin du dossier vers le fichier xml
        self.dossierDuFichierXml = os.path.abspath(
            os.path.dirname(fichierMenus))
        self.lireMenusXml(fichierMenus)
        # Fin initGui()

    def fenetreParam(self):
        msgBox = QMessageBox(self.iface.mainWindow())
        msgBox.setWindowTitle(
            self.tr("Plugin: Create menus  (version %s)") % version)

        # okButton = msgBox.addButton(self.tr("Close"), QMessageBox.RejectRole)

        PluginPath = os.path.normcase(
            os.path.normpath(os.path.realpath(os.path.dirname(__file__))))
        s = QSettings()
        fic = s.value("PluginCreerMenus/fileMenus", "")
        racine = os.path.abspath(os.path.dirname(fic))

        # premier démarrage de l'extension ou parametre incorrect
        if not os.path.isfile(fic):
            msgBox.setText(self.tr(
                "<strong>The file that contains the description of the menus is not defined !</strong>"))
            changeButton = msgBox.addButton(
                self.tr("Choose a file"), QMessageBox.AcceptRole)
            racine = os.path.normpath(PluginPath + "/../../..")
        else:
            msgBox.setText(
                "<strong>" + self.tr("The file that contains the description of the menus is:") + "</strong><br>" + fic)
            changeButton = msgBox.addButton(
                self.tr("Choose another file"), QMessageBox.AcceptRole)

        modelButton = msgBox.addButton(
            self.tr("Create from template"), QMessageBox.AcceptRole)
        aideButton = msgBox.addButton(self.tr("Help"), QMessageBox.HelpRole)
        msgBox.setToolTip("""<p><font face="Helvetica, Arial, sans-serif">{}</p><br /><br /><br />""".format(
            self.tr("At its first start, the plugin copies a template file <strong>Menus.xml</strong> "
                    "to the folder <u>USERPROFILE/.qgis2</u>. It adds a menu <u>Shortcuts</u> with a few examples "
                    "of layers.</p> <p>This is the file to edit to create your menus. You can move that file to "
                    "another folder then press button <u>Choose another file</u> to point the plugin to its new place.")))

        # pour ne pas afficher le bouton "Editer" si le module Qsci n'est pas
        # installé
        try:
            from PyQt4.Qsci import QsciScintilla
            editButton = msgBox.addButton(
                self.tr("Edit"), QMessageBox.AcceptRole)
        except:
            editButton = 0

        while True:
            msgBox.exec_()
            if msgBox.clickedButton() == changeButton:
                fileName = QFileDialog.getOpenFileName(
                    self.iface.mainWindow(), "Choisir le fichier des menus", racine)
                if fileName == "":
                    continue  # si appuyé sur Annuler, ré-afficher msgBox
                s.setValue("PluginCreerMenus/fileMenus", fileName)
                msgBox.setText(
                    u"Le fichier qui contient la description des menus se trouve ici :\n" + fileName)
                self.unload()
                self.initGui()
                continue
            #
            # copier le modele vers l'emplacement choisi
            elif msgBox.clickedButton() == modelButton:
                fileName = QFileDialog.getSaveFileName(self.iface.mainWindow(), u"Placer votre fichier (copie du modèle)",
                                                       racine + os.sep + "Menus.xml")
                if fileName == "":
                    continue  # si appuyé sur Annuler: ré-afficher msgBox
                # s'il y a déjà un fichier, le supprimer :
                if QFile.exists(fileName):
                    # si la suppression échoue :
                    if not QFile.remove(fileName):
                        msgBox.setText(
                            u"La copie du modèle a échoué.\n Merci de choisir un autre dossier ou un autre nom de fichier.")
                        continue
                # si la copie a echoue
                if not QFile.copy(PluginPath + os.sep + "Menus.xml.modele", fileName):
                    msgBox.setText(u"La copie du modèle a échoué...")
                    continue
                s.setValue("PluginCreerMenus/fileMenus", fileName)
                msgBox.setText(
                    u"Le fichier qui contient la description des menus se trouve ici :\n" + fileName)
                self.unload()
                self.initGui()
                continue
            #
            elif msgBox.clickedButton() == editButton:  # voir le XML
                editor = xmlEditor(self.iface.mainWindow(), fic, self.reload)
                try:  # si le module Qsci n'est pas installé ça bug
                    editor.resize(800, 500)
                    editor.setWindowTitle(u"Fichier: " + fic)
                    editor.show()
                    if editor.exec_():
                        editor.apply_changes()
                    break
                except:
                    pass
                continue
            #
            elif msgBox.clickedButton() == aideButton:
                self.fenetreAide(True)
                continue
            #
            else:
                break  # bouton Fermer

            # verifier que fileName n'est pas dans le dossier du plugin (sera
            # effacé par update) !!
            fileDir = os.path.normcase(
                os.path.normpath(os.path.realpath(os.path.dirname(fileName))))
            if PluginPath == fileDir:
                msgBox.setText(
                    u"Désolé, vous ne pouvez pas placer votre fichier dans le dossier du plugin.")
                # retour à la valeur precedente
                s.setValue("PluginCreerMenus/fileMenus", fic)
            else:
                break
        # Fin fenetreParam()

    def fenetreAide(self, modal=False):
        form = QDialog(self.iface.mainWindow())
        form.setWindowTitle(
            u"Mode d'emploi de l'extension : Créer ses propres menus")
        fen = QtWebKit.QWebView(form)
        Layout_1 = QGridLayout(form)
        Layout_1.setContentsMargins(0, 0, 0, 0)
        Layout_1.addWidget(fen, 0, 0, 1, 1)
        fen.setUrl(QUrl(self.path + os.sep + "Aide.html"))
        if modal:
            form.exec_()  # pour le bouton Aide dans la fenetreParam
        else:
            form.show()
        # Fin fenetreAide()

    def lireMenusXml(self, fichier):
        f = QFile(fichier)
        if not f.open(QIODevice.ReadOnly):
            return
        doc = QtXml.QDomDocument()
        doc.setContent(f)
        root = doc.documentElement()
        # les espaces, tab, retour ligne à supprimer au début et à la fin
        # rm = QRegExp("^[\n\r\t\s]*|[\n\r\t\s]*$")

        options = root.firstChildElement('options')  # traiter les options
        if not options.isNull():
            elms = options.childNodes()
            for i in range(elms.length()):  # parcourir toutes les options
                elm = elms.item(i).toElement()

                if elm.tagName() == "AjoutMenu":
                    # .remove(rm) # le texte de la balise sans les éventuels espaces avant et après
                    base = elm.text().strip(' \t\n\r')
                    if base == "Extension":
                        self.affichage = self.iface.pluginMenu()
                    elif base == "Couche":
                        self.affichage = self.iface.layerMenu()
                    elif base == "Database":
                        self.affichage = self.iface.databaseMenu()
                    else:
                        # dans le menu Principal de Qgis
                        self.affichage = self.iface.mainWindow().menuBar()

                elif elm.tagName() == "MenusCommuns":
                    # .remove(rm) # le texte de la balise sans les éventuels espaces avant et après
                    MenusCommuns = elm.text().strip(' \t\n\r')
                    # tester avec un chemin relatif au fichier XML :
                    if not os.path.isfile(MenusCommuns):
                        MenusCommuns = self.dossierDuFichierXml + \
                            os.sep + MenusCommuns
                    if not os.path.isfile(MenusCommuns):
                        continue
                    # sauvegarde le chemin du dossier actuel
                    oldDossierDuFichierXml = self.dossierDuFichierXml
                    # le dossier du fichier MenusCommuns
                    dossier = os.path.abspath(os.path.dirname(MenusCommuns))
                    # chemin pour trouver les fichiers relatifs à ce Xml dans
                    # traiterAction()
                    self.dossierDuFichierXml = dossier
                    self.lireMenusXml(MenusCommuns)
                    # retablit le chemin
                    self.dossierDuFichierXml = oldDossierDuFichierXml

                elif elm.tagName() == "barre":
                    self.afficherBarre(
                        elm.attribute('nom'), elm.attribute('afficher'))
        # une fois que les éventuelles options ont été traitées, il faut
        # parcourir les menus :
        self.traiterMenu(root, self.affichage)
        f.close()
        # Fin lireMenusXml()

    def traiterMenu(self, elemXML, parent):
        """ fonction récursive qui parcourt chaque menu """
        elms = elemXML.childNodes()
        for i in range(elms.length()):
            elm = elms.item(i).toElement()

            if elm.tagName() == "menu":
                txtmenu = elm.attribute('nom')
                monQmenu = parent.addMenu(txtmenu)
                self.refqm.append(monQmenu)
                self.traiterMenu(elm, monQmenu)

            elif elm.tagName() == u"séparateur":
                parent.addSeparator()

            elif elm.tagName() == "action":
                self.traiterAction(elm, parent)
        # Fin traiterMenu()

    def traiterAction(self, elm, menu):
        nom = elm.attribute('nom')
        if nom == '':
            return  # l'action a été mal rédigée
        newaction = QAction(nom, self.iface.mainWindow())
        # les espaces, tab, retour ligne à supprimer au début et à la fin
        # rm = QRegExp("^[\n\r\t\s]*|[\n\r\t\s]*$")

        type = elm.attribute('type').lower()
        if type == 'vecteur':
            # .remove(rm) # le texte de la balise sans les éventuels espaces avant et après
            val = elm.text().strip(' \t\n\r')
            # si val not fichier, on teste avec le chemin relatif au fichier
            # xml
            if not os.path.isfile(val):
                val = self.dossierDuFichierXml + os.sep + val
            if not os.path.isfile(val):
                return
            tip = "Couche: " + val
            fonction = self.afficheVecto
            # le nom du fichier sans son extension
            nomfic = os.path.splitext(os.path.basename(val))[0]
            # s'il existe un fichier de style pour cette couche (dans le meme
            # dossier que le ficheir xml)
            if os.path.isfile(self.dossierDuFichierXml + os.sep + nomfic + '.qml'):
                newaction.setToolTip(
                    self.dossierDuFichierXml + os.sep + nomfic + '.qml')
            else:
                newaction.setToolTip("0")  # setToolTip("") ne marche pas !
            newaction.setIcon(QIcon(self.icons + "vecteur.png"))

        elif type == 'qlr':
            # .remove(rm) # le texte de la balise sans les éventuels espaces avant et après
            val = elm.text().strip(' \t\n\r')
            # si val not fichier, on teste avec le chemin relatif au fichier
            # xml
            if not os.path.isfile(val):
                val = self.dossierDuFichierXml + os.sep + val
            if not os.path.isfile(val):
                return
            tip = "Couche: " + val
            fonction = self.afficheQlr
            newaction.setIcon(QIcon(self.icons + "multi.png"))

        elif type == 'spatialite':
            # le texte de la balise sans les éventuels espaces avant et après
            val = elm.text().strip(' \t\n\r')
            tip = "Table: " + val
            fonction = self.afficheSpatialite
            newaction.setIcon(QIcon(self.icons + "vecteur.png"))

        elif type == 'postgres':
            # le texte de la balise sans les éventuels espaces avant et après
            val = elm.text().strip(' \t\n\r')
            tip = "Table: " + val
            fonction = self.affichePostgres
            newaction.setIcon(QIcon(self.icons + "vecteur.png"))

        elif type == 'raster':
            val = elm.text().strip(' \t\n\r')  # .remove(rm)
            # si val not fichier, on teste avec le chemin relatif au fichier
            # xml
            if not os.path.isfile(val):
                val = self.dossierDuFichierXml + os.sep + val
            if not os.path.isfile(val):
                return
            tip = "Couche: " + val
            fonction = self.afficheRaster
            # le nom du fichier sans son extension
            nomfic = os.path.splitext(os.path.basename(val))[0]
            # s'il existe un fichier de style pour cette couche (dans le meme
            # dossier que le ficheir xml)
            if os.path.isfile(self.dossierDuFichierXml + os.sep + nomfic + '.qml'):
                newaction.setToolTip(
                    self.dossierDuFichierXml + os.sep + nomfic + '.qml')
            else:
                newaction.setToolTip("0")  # setToolTip("") ne marche pas !
            newaction.setIcon(QIcon(self.icons + "raster.png"))

        elif type == 'wms':
            url = elm.firstChildElement('url')
            if url.isNull():
                return
            val = url.text().strip(' \t\n\r')  # .remove(rm)
            couche = elm.firstChildElement('couche')
            if couche.isNull():
                return
            val = val + "||" + couche.text().strip(' \t\n\r')  # .remove(rm)
            format = elm.firstChildElement('format')
            if format.isNull():
                val = val + "||image/png"
            else:
                # .remove(rm)
                val = val + "||" + format.text().strip(' \t\n\r')
            scr = elm.firstChildElement('scr')
            if scr.isNull():
                val = val + "||EPSG:2154"
            else:
                val = val + "||" + scr.text().strip(' \t\n\r')  # .remove(rm)
            fonction = self.afficheWMS
            tip = "WMS: " + val
            newaction.setIcon(QIcon(self.icons + "wms.png"))

        elif type == 'wfs':
            url = elm.firstChildElement('url')
            if url.isNull():
                return
            val = url.text().strip(' \t\n\r')  # .remove(rm)
            # version du protocol WFS
            version = elm.firstChildElement('version')
            if version.isNull():
                val = val + "||1.0.0"  # vaeur par defaut: 1.0.0
            else:
                # .remove(rm)
                val = val + "||" + version.text().strip(' \t\n\r')

            couche = elm.firstChildElement('couche')  # nom de la couche
            if couche.isNull():
                return
            val = val + "||" + couche.text().strip(' \t\n\r')  # .remove(rm)

            scr = elm.firstChildElement('scr')  # projection
            if scr.isNull():
                val = val + "||EPSG:2154"
            else:
                val = val + "||" + scr.text().strip(' \t\n\r')  # .remove(rm)
            # determine si qgis telecharge toute la couche à l'ouverture
            cache = elm.firstChildElement('cache')
            if cache.isNull():
                # valeur par defaut: non (telecharger en fonction des zooms)
                val = val + "||non"
            elif cache.text().strip(' \t\n\r') == 'oui':
                # telecharger toute la couche à l'ouverture
                val = val + "||oui"
            else:
                val = val + "||non"
            fonction = self.afficheWFS
            tip = "WFS: " + val
            newaction.setIcon(QIcon(self.icons + "wfs.png"))

        elif type == 'projet':  # ouvrir projet qgis .qgs
            val = elm.text().strip(' \t\n\r')  #
            # si val pas trouvé, on teste avec le chemin relatif au fichier xml
            if not QFile(val).exists():
                val = self.dossierDuFichierXml + os.sep + val
            if not QFile(val).exists():
                return
            # remplace le travail en cours par ce projet
            fonction = self.afficheProjet
            tip = "Tout fermer et ouvrir: " + val
            newaction.setIcon(QIcon(self.icons + "proj.png"))

        elif type == 'multi':  # ajouter les couches d'un projet qgis
            val = elm.text().strip(' \t\n\r')  #
            # si val pas trouvé, on teste avec le chemin relatif au fichier xml
            if not QFile(val).exists():
                val = self.dossierDuFichierXml + os.sep + val
            if not QFile(val).exists():
                return
            # intègre les couches du projet dans le travail en cours
            fonction = self.integrerProjet
            tip = u"Intégrer le projet: " + val
            newaction.setIcon(QIcon(self.icons + "multi.png"))

        elif type == 'web':
            val = elm.text().strip(' \t\n\r')  #
            fonction = self.afficheWeb
            tip = val
            newaction.setIcon(QIcon(self.icons + "web.png"))

        elif type == 'fichier':
            val = elm.text().strip(' \t\n\r')  #
            # ça permet d'indiquer un répertoire qui s'ouvrira avec
            # l'explorateur Windows
            if not os.path.exists(val):
                # si val not fichier, on teste avec le chemin relatif au
                # fichier xml
                val = self.dossierDuFichierXml + os.sep + val
            if not os.path.exists(val):
                return
            fonction = self.afficheAutreFichier
            tip = "Ouvrir: " + val
            newaction.setIcon(QIcon(self.icons + "file.png"))

        elif type == 'python':
            val = elm.text().strip(' \t\n\r')  #
            # si val not fichier, on teste avec le chemin relatif au fichier
            # xml
            if not os.path.isfile(val):
                val = self.dossierDuFichierXml + os.sep + val
            if not os.path.isfile(val):
                return
            fonction = self.execPython
            tip = "Exec. le code: " + val
            newaction.setIcon(QIcon(self.icons + "python.png"))

        else:
            return

        # astuce pour faire récupérer le nom du fichier dans la fonction
        # affiche...
        newaction.setWhatsThis(val)
        newaction.setStatusTip(tip)
        QObject.connect(newaction, SIGNAL("triggered()"), fonction)
        menu.addAction(newaction)
        # Fin traiterAction()

    # Merci à Christophe MASSE pour ce code :
    def afficherBarre(self, cle, val):
        dictActions = {"BarreAide": "mHelpToolBar", "BarreAttribut": "mAttributesToolBar", "BarreCouches": "mLayerToolBar",
                       "BarreEtiquette": "mLabelToolBar", "BarreFichier": "mFileToolBar", "BarreGRASS": "GRASS",
                       "BarreNavig": "mMapNavToolBar", "BarreNum": "mDigitizeToolBar", u"BarreNumAvancée": "mAdvancedDigitizeToolBar",
                       "BarrePlugin": "mPluginToolBar", "BarrePlugin": "mPluginToolBar", "BarreRaster": "mRasterToolBar",
                                      "BarreVecteur":  "mVectorToolBar", "BarreBase":  "mDatabaseToolBar", "BarreInternet": "mWebToolBar"
                       }

        if cle in dictActions:
            return
        else:
            param = dictActions[cle]
        Qbarre = self.iface.mainWindow().findChild(QToolBar, param)
        if not Qbarre:
            return
        if val.lower() == "n":
            Qbarre.hide()
        elif val.lower() == "o":
            Qbarre.show()
        # Fin afficherBarre

    def afficheVecto(self):
        i = self.iface
        lemenu = QObject.sender(i)
        i.mapCanvas().setRenderFlag(False)
        macouche = i.addVectorLayer(
            QAction.whatsThis(lemenu), QAction.text(lemenu), "ogr")
        # le chemin d'un éventuel qml est dans le toolTip
        if macouche and not QAction.toolTip(lemenu) == "0":
            try:
                macouche.loadNamedStyle(QAction.toolTip(lemenu))
            except:
                pass
        i.mapCanvas().setRenderFlag(True)
        # Fin afficheVecto()

    def afficheQlr(self):  # Merci à Frédéric MUZZOLON pour ce code :
        i = self.iface
        lemenu = QObject.sender(i)
        path = QAction.whatsThis(lemenu)
        with open(path, 'r') as f:
            content = f.read()
            doc = QtXml.QDomDocument()
            doc.setContent(content)
            layernode = doc.elementsByTagName('maplayer').at(0)
            layerelm = layernode.toElement()
            layertype = layerelm.attribute("type")
            layer = None
            if layertype == "vector":
                layer = QgsVectorLayer()
            elif layertype == 'raster':
                layer = QgsRasterLayer()
            ok = layer.readLayerXML(layerelm)
            if ok:
                QgsMapLayerRegistry.instance().addMapLayer(layer)
        # Fin afficheQlr()

    def afficheSpatialite(self):
        i = self.iface
        lemenu = QObject.sender(i)
        i.mapCanvas().setRenderFlag(False)
        i.addVectorLayer(QAction.whatsThis(lemenu), QAction.text(lemenu), "spatialite")
        i.mapCanvas().setRenderFlag(True)
        # Fin afficheSpatialite()

    def affichePostgres(self):
        i = self.iface
        lemenu = QObject.sender(i)
        i.mapCanvas().setRenderFlag(False)
        i.addVectorLayer(QAction.whatsThis(lemenu), QAction.text(lemenu), "postgres")
        # if macouche and not QAction.toolTip(lemenu)=="0": # le chemin d'un éventuel qml est dans le toolTip
        #  try: macouche.loadNamedStyle( QAction.toolTip(lemenu) )
        #  except: pass
        i.mapCanvas().setRenderFlag(True)
        # Fin affichePostgres()

    def afficheRaster(self):
        i = self.iface
        lemenu = QObject.sender(i)
        i.mapCanvas().setRenderFlag(False)
        if QGis.QGIS_VERSION_INT < 20400:  # pour qgis jusqu'à 2.2.x
            macouche = i.addRasterLayer(
                QAction.whatsThis(lemenu), QAction.text(lemenu))
        else:
            macouche = QgsRasterLayer(
                QAction.whatsThis(lemenu), QAction.text(lemenu))
            # prête à être utilisée mais pas encore affichée
            QgsMapLayerRegistry.instance().addMapLayer(macouche, False)
            legendTree = self.iface.layerTreeView()
            # on veut ajouter la couche dans le groupe actif
            grp = legendTree.currentGroupNode()
            if not grp:
                # sinon à la base de la légende
                grp = QgsProject.instance().layerTreeRoot()
            grp.addLayer(macouche)  # ajouter à la fin car c'est du raster !
        # le chemin d'un éventuel qml est dans le toolTip
        if macouche and not QAction.toolTip(lemenu) == "0":
            try:
                macouche.loadNamedStyle(QAction.toolTip(lemenu))
            except:
                pass
        i.mapCanvas().setRenderFlag(True)
        # Fin afficheRaster()

    def afficheProjet(self):
        i = self.iface
        action = QObject.sender(i)
        msgBox = QMessageBox(i.mainWindow())
        msgBox.setWindowTitle("Ouvrir un projet QGIS")
        msgBox.setText(
            u"<strong>Projet : " + QAction.whatsThis(action) + "</strong>")
        ouvreButton = msgBox.addButton(
            u"Fermer tout et ouvrir ce projet", QMessageBox.AcceptRole)
        ajoutButton = msgBox.addButton(
            u"Intégrer les couches de ce projet", QMessageBox.AcceptRole)
        msgBox.addButton(u"Annuler", QMessageBox.RejectRole)
        msgBox.setDefaultButton(ajoutButton)
        while True:
            msgBox.exec_()
            if msgBox.clickedButton() == ouvreButton:
                self.iface.mapCanvas().setRenderFlag(False)
                i.addProject(QAction.whatsThis(action))
                self.iface.mapCanvas().setRenderFlag(True)
            elif msgBox.clickedButton() == ajoutButton:
                self.integrerProjet(action)
            break  # touche Echap ou Fermeture du msgBox
        # Fin afficheProjet()

    def integrerProjet(self, action=None):
        """ fonction qui peut etre lancé par un menu (action=None)
            ou à partir de afficheProjet (action=action_qui_a_exec_afficheProjet) """
        if not action:
            action = QObject.sender(self.iface)
        fichier = QAction.whatsThis(action)
        f = QFile(fichier)
        if not f.open(QIODevice.ReadOnly):
            return
        li = self.iface.legendInterface()
        self.iface.mapCanvas().setRenderFlag(False)
        doc = QtXml.QDomDocument()
        doc.setContent(f)
        # definition de chaque couche (fichier, style, etiquette...)
        maps = doc.elementsByTagName("maplayer")
        nodeListe = doc.elementsByTagName("legend")
        # le contenu de la legende, dans le projet Qgis à afficher
        legende = nodeListe.item(0)

    def lireGroupe22(domGrp, treeGrp):  # valid jusqu'à qgis 2.2
        elems = domGrp.childNodes()
        # parcourir les couches du groupe en partant de la dernière
        for N in range(elems.length() - 1, -1, -1):
            ele = elems.item(N).toElement()

            if ele.tagName() == "legendgroup":
                nomGrpe = ele.attribute("name")
                index = li.addGroup(nomGrpe, True, treeGrp)
                # ! mais l'élément actif n'est pas toujours le groupe qu'on vient d'ajouter...
                new = legendTree.currentItem()
                # si l'element actif dans la legende n'est pas le groupe qu'on
                # vient d'ajouter
                if not new.text(0) == nomGrpe:
                    # l'element actif est peut-etre le groupe parent du groupe
                    # qu'on vient d'ajouter
                    if new.childCount() > 0:
                        # est-ce que le 1er fils de l'element actif est le
                        # groupe qu'on vient d'ajouter?
                        if new.child(0).text(0) == nomGrpe:
                            new = new.child(0)
                parent = new.parent()
                if parent:  # si groupe ajouté dans un groupe
                    idNew = parent.indexOfChild(new)
                    treeItem = parent.takeChild(idNew)  # couper
                else:  # si groupe ajouté à la racine de la légende
                    idNew = legendTree.indexOfTopLevelItem(new)
                    treeItem = legendTree.takeTopLevelItem(idNew)  # couper
                # coller en 1ere position dans le groupe
                treeGrp.insertChild(0, treeItem)
                treeItem.setExpanded(True)
                lireGroupe22(ele, treeItem)
                continue

            if not ele.tagName() == "legendlayer":
                continue
            nodeListe = ele.elementsByTagName("legendlayerfile")
            if not nodeListe.length() == 1:
                continue
            layId = nodeListe.item(0).toElement().attribute("layerid")
            # rechercher dans les couches du projet celle qui a layId
            for i in range(maps.length()):
                coucheId = maps.item(i).firstChildElement("id")
                if not layId == coucheId.toElement().text():
                    continue
                nomCouche = maps.item(i).firstChildElement(
                    "layername").toElement().text()
                QgsProject.instance().read(maps.item(i))  # ajouter la couche
                # ! mais l'élément actif n'est pas toujours la couche qu'on vient d'ajouter...
                new = legendTree.currentItem()
                # QMessageBox.about( self.iface.mainWindow(), "currentItem : "+
                # new.text(0), "nomCouche : "+ nomCouche ) ###
                # l'element actif dans la legende est peut-etre le dossier
                # parent:
                if not new.text(0) == nomCouche:
                    if new.childCount() == 0:
                        break  # pas un dossier ou dossier vide
                    if new.child(0).text(0) == nomCouche:
                        new = new.child(0)
                    else:
                        # le 1er element du dossier n'est pas la couche qu'on
                        # vient d'ajouter
                        break
                new.setExpanded(False)
                if ele.attribute("checked") == "Qt::Unchecked":
                    # retablie l'etat: affiché ou non
                    new.setCheckState(0, Qt.Unchecked)
                # Placer cette couche en 1ere position dans son groupe :
                parent = new.parent()
                if parent:  # couche ajoutée dans un groupe
                    idNew = parent.indexOfChild(new)
                    if idNew == 0 and parent == treeGrp:
                        break  # deja a la bonne place
                    treeItem = parent.takeChild(idNew)  # couper
                else:  # couche ajoutée à la racine de la légende
                    idNew = legendTree.indexOfTopLevelItem(new)
                    treeItem = legendTree.takeTopLevelItem(idNew)  # couper
                # coller en 1ere position dans le groupe
                treeGrp.insertChild(0, treeItem)
                break

    def lireGroupe(domGrp, treeGrp):
        elems = domGrp.childNodes()
        # parcourir les couches du groupe en partant de la dernière
        for N in range(elems.length() - 1, -1, -1):
            ele = elems.item(N).toElement()

            if ele.tagName() == "legendgroup":
                nomGrpe = ele.attribute("name")
                treeItem = treeGrp.insertGroup(0, nomGrpe)
                treeItem.setExpanded(True)
                lireGroupe(ele, treeItem)
                continue

            if not ele.tagName() == "legendlayer":
                continue
            nodeListe = ele.elementsByTagName("legendlayerfile")
            if not nodeListe.length() == 1:
                continue
            layId = nodeListe.item(0).toElement().attribute("layerid")
            # rechercher dans les couches du projet celle qui a layId
            for i in range(maps.length()):
                coucheId = maps.item(i).firstChildElement("id")
                if not layId == coucheId.toElement().text():
                    continue
                nomCouche = maps.item(i).firstChildElement(
                    "layername").toElement().text()
                QgsProject.instance().read(maps.item(i))  # ajouter la couche
                # ! mais l'élément actif n'est pas toujours la couche qu'on vient d'ajouter...
                new = legendTree.currentLayer()
                # l'element actif dans la legende est peut-etre le dossier
                # parent:
                if not new or not new.originalName() == nomCouche:
                    # cherche la couche dans le groupe
                    new = legendTree.currentGroupNode().findLayer(coucheId)
                    if not new:
                        break  # pas trouvé
                else:
                    new = legendTree.currentNode()
                new.setExpanded(False)
                if ele.attribute("checked") == "Qt::Unchecked":
                    # retablie l'etat: affiché ou non
                    new.setVisible(Qt.Unchecked)

                # Placer cette couche dans son groupe :
                if new.parent() == treeGrp:
                    break  # deja dans le bon groupe
                # new.parent().children().index(new) #position
                clone = new.clone()
                treeGrp.insertChildNode(0, clone)  # en 1ere position
                par = new.parent()
                par.removeChildNode(new)
                break

        if QGis.QGIS_VERSION_INT < 20400:  # pour qgis jusqu'à 2.2.x
            li.addGroup("Ouverture des couches en cours...")
            legendTree = self.iface.mainWindow().findChild(
                QDockWidget, "Legend").findChild(QTreeWidget)
            index = legendTree.indexOfTopLevelItem(legendTree.currentItem())
            # le nouveau groupe dans lequel on va inserer les couches du projet
            groupe0 = legendTree.takeTopLevelItem(index)
            # deplace le nouveau groupe tout en haut
            legendTree.insertTopLevelItem(0, groupe0)
            legendTree.setCurrentItem(groupe0)
            groupe0.setExpanded(True)
            lireGroupe22(legende, groupe0)
            groupe0.setText(0, QAction.text(action))

        else:  # pour qgis 2.4 et plus
            legendTree = self.iface.layerTreeView()
            # #legendTree = self.iface.mainWindow().findChild(QDockWidget, "Layers").findChild(QgsLayerTreeView)
            treeRoot = QgsProject.instance().layerTreeRoot()
            # treeRoot = legendTree.currentGroupNode()
            # while treeRoot.parent(): #cherche la racine de la legende
            #  treeRoot = treeRoot.parent()
            groupe0 = treeRoot.insertGroup(
                0, "Ouverture des couches en cours...")
            groupe0.setExpanded(True)
            lireGroupe(legende, groupe0)
            groupe0.setName(QAction.text(action))

        # ##self.iface.messageBar().pushMessage("..", "nb legend : "+ str(nodeListe.length()), level=0, duration=3)
        f.close()
        self.iface.mapCanvas().setRenderFlag(True)
        # Fin integrerProjet()

    def afficheWMS(self):
        i = self.iface
        lemenu = QObject.sender(i)
        nomCouche = QAction.text(lemenu)
        sep = "||"  # séparateur: ||
        val = QAction.whatsThis(lemenu)
        lUri = val.split(sep)
        # c'est un simple lien web --> afficher dans un navigateur
        if len(lUri) == 1:
            try:
                os.startfile(val)  # ne fonctionne qu'avec Windows
            except:
                pass
            return
        if len(lUri) != 4:
            return  # WMS mal défini

        try:
            uri = u"url=" + lUri[0]
            uri = uri + "&layers=" + lUri[1]
            uri = uri + "&format=" + lUri[2]  # 'image/png'
            uri = uri + "&crs=" + lUri[3]  # 'EPSG:2154'
            uri = uri + "&styles="
            macouche = i.addRasterLayer(uri, nomCouche, 'wms')
        except:
            pass
        # Fin afficheWMS()

    def afficheWFS(self):
        i = self.iface
        lemenu = QObject.sender(i)
        nomCouche = QAction.text(lemenu)
        sep = "||"  # séparateur: ||
        val = QAction.whatsThis(lemenu)
        lUri = val.split(sep)
        if len(lUri) != 5:
            return  # WFS mal défini
        uri = ""
        try:
            uri = lUri[0] + "?SERVICE=WFS&VERSION="
            uri = uri + lUri[1] + "&REQUEST=GetFeature&TYPENAME="
            uri = uri + lUri[2]
            uri = uri + "&SRSNAME=" + lUri[3]
            cache = lUri[4]
            if cache == "non":
                # BBOX bidon qui empeche Qgis de mettre toute la couche en
                # cache dés l'ouverture
                uri = uri + "&BBOX=0,0,1,1"
            i.addVectorLayer(uri, nomCouche, "WFS")
        except:
            QMessageBox.warning(self.iface.mainWindow(), "Echec de l'ouverture de la couche WFS",
                                u"URL utilisée :\n" + uri[:80] + "\n" + uri[80:160] + "\n" + uri[160:])
        # Fin afficheWFS()

    def afficheWeb(self):
        lemenu = QObject.sender(self.iface)
        try:
            # ne fonctionne qu'avec Windows
            os.startfile(QAction.whatsThis(lemenu))
        except:
            pass
        # Fin afficheWeb()

    def afficheAutreFichier(self):
        lemenu = QObject.sender(self.iface)
        fichier = QAction.whatsThis(lemenu)
        try:
            os.startfile(fichier)  # ne fonctionne qu'avec Windows
        except:
            pass
        # Fin afficheAutreFichier()

    def execPython(self):
        choix = QObject.sender(self.iface)
        fichier = QAction.whatsThis(choix)
        # le nom du fichier sans son extension
        nomfic = os.path.splitext(os.path.basename(fichier))[0]
        module = imp.load_source(nomfic, fichier)
        module.action(self.iface)
        # Fin execPython()

    def reload(self):
        self.unload()
        self.initGui()

    def unload(self):
        # supprimer le "Menus perso" du menu Extension :
        self.extensionMenuPerso.parentWidget().removeAction(
            self.extensionMenuPerso.menuAction())
        # supprimer les menus du xml :
        for m in self.refqm:
            m.parentWidget().removeAction(m.menuAction())
