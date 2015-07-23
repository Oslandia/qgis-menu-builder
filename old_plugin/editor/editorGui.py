# -*- coding: utf-8 -*-
""" -----------------------------------------------
 basé sur le code de : Eli Bendersky (eliben@gmail.com)
 --> qsci_simple_pythoneditor.pyw
 This code is in the public domain
 -------------------------------------------------- """
import codecs, os.path
from PyQt4 import QtCore, QtGui, QtWebKit

class xmlEditor(QtGui.QDialog):
  ARROW_MARKER_NUM = 8
  def __init__(self, parent, fichier, foncReload):
    try:
      from PyQt4 import Qsci
      from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerXML
    except:
      QtGui.QMessageBox.critical( parent, "Echec",
       u"L'éditeur de code est introuvable.\nLe module 'QScintilla' n'est pas installé.")
      return

    self.reload = foncReload # fonction qui met à jour les menus (à appeler quand on enregistre le fichier xml)
    self.fichier = fichier
    flags = QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowStaysOnTopHint
    QtGui.QDialog.__init__(self, parent, flags)
    self.ed = QsciScintilla(self)
    gridLayout1 = QtGui.QGridLayout(self)
    gridLayout1.setContentsMargins( 0, 0, 0, 0 )
    hLayout2 = QtGui.QHBoxLayout()
    gridLayout1.addLayout(hLayout2, 0, 0)
    gridLayout1.addWidget(self.ed, 1, 0) #, 1, 1)
    bSave = QtGui.QPushButton(u'Enregistrer !')
    bSave.clicked.connect(self.saveChanges)
    bSave.setToolTip(u"<p>Sauvegarder les modifications apportées au fichier<br />puis appliquer ces changements dans les menus.</p><br /><br /><br />")
    hLayout2.addWidget(bSave)

    self.bAide = QtGui.QPushButton(u'Aide',self)
    self.bAide.clicked.connect(self.aide)
    hLayout2.addWidget(self.bAide)
    self.ed.setUtf8(True) # permet saisie des accents (requis meme pour cp1252)

    lexer = QsciLexerXML(self) # Choose a lexer
    api = Qsci.QsciAPIs(lexer)
    api.prepare() # Compile the api for use in the lexer
    # Tell the editor we are using any installed APIs for the autocompletion
    self.ed.setAutoCompletionSource(QsciScintilla.AcsAPIs)
    # Set the length of the string before the editor tries to autocomplete
    self.ed.setAutoCompletionThreshold(2)
    self.ed.setLexer(lexer)

    font = QtGui.QFont() # Set the default font
    font.setFamily('Courier')
    font.setFixedPitch(True)
    font.setPointSize(12)
    self.ed.setFont(font)

    font.setFamily('Helvetica')
    font.setPointSize(9)
    self.ed.setMarginsFont(font)
    large = '9999'
    self.ed.setMarginWidth(0, large) # Margin 0 is used for line numbers
    self.ed.setMarginLineNumbers(0, True)
    self.ed.setMarginWidth(1,1) # la marge entre num lignes et blocs

    self.ed.setMarginsBackgroundColor(QtGui.QColor("#cccccc"))
    # Brace matching: enable for a brace immediately before or after the current position :
    self.ed.setBraceMatching(QsciScintilla.SloppyBraceMatch)
    # Current line visible with special background color :
    self.ed.setCaretLineVisible(True)
    self.ed.setCaretLineBackgroundColor(QtGui.QColor("#ffe4e4"))

    # Use raw message to Scintilla here (all messages are documented here:  http://www.scintilla.org/ScintillaDoc.html)
    self.ed.setTabWidth(2) # tab=2 car
    self.ed.setIndentationsUseTabs(False) # remplace tabs par car
    self.ed.setIndentationWidth(0) # indent = tabWidth
    self.ed.setTabIndents(True) #tab key will indent a line rather than insert a tab character
    self.ed.setBackspaceUnindents(True) #backspace key will unindent a line
    self.ed.setAutoIndent( True )
    self.ed.setIndentationGuides( True )
    self.ed.setFolding(QsciScintilla.BoxedTreeFoldStyle) # Folding visual : we will use boxes
    self.ed.setFoldMarginColors(QtGui.QColor("#99CC66"),QtGui.QColor("#AAAAAA"))

    self.ed.setWrapMode( QsciScintilla.WrapWord )
    self.ed.setWrapIndentMode( QsciScintilla.WrapIndentSame )

    self.ed.setText( codecs.open(fichier,'r','cp1252','replace').read() ) # Show this file in the editor
    #Fin __init__()

  def aide(self):
    form = QtGui.QDialog(self)
    form.setWindowTitle(u"Mode d'emploi de l'extension : Créer Menus")
    fen = QtWebKit.QWebView(form)
    Layout_1 = QtGui.QGridLayout(form)
    Layout_1.setContentsMargins( 0, 0, 0, 0 )
    Layout_1.addWidget(fen, 0, 0, 1, 1)
    PluginPath = os.path.abspath(os.path.dirname(__file__))
    fen.setUrl( QtCore.QUrl(PluginPath +"/../Aide.html") )
    form.show() #form.exec_()
    #Fin fenetreAide()

  def saveChanges(self, checked=False):
    with codecs.open(self.fichier,'w','cp1252') as f:
      f.write( self.ed.text() )
    self.reload()

  def on_margin_clicked(self, nmargin, nline, modifiers):
    # Toggle marker for the line the margin was clicked on
    if self.ed.markersAtLine(nline) != 0:
      self.ed.markerDelete(nline, self.ARROW_MARKER_NUM)
    else:
      self.ed.markerAdd(nline, self.ARROW_MARKER_NUM)
