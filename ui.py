#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Name: tagcoder
# Description: This is mp3 tag editor with convenient encode options

def msg(m):
	w.statusBar.showMessage( unicode( m ) )

def msgexc():
	(type, val, tb) = sys.exc_info()
	traceback.print_exception(type, val, tb)
	msg( ''.join( traceback.format_exception_only(type,val) ) )

### Buttons ---------------------------------------
### -----------------------------------------------

def openButton(this):
	addItems( [ unicode( f ) for f in QFileDialog.getOpenFileNames(w,u"open music files") ] )

def typeDec():
	if w.decoderEditor.text() == "":
		w.decoderEditor.setText('utf-8')
	return unicode( w.decoderEditor.text() )

def typeEnc():
	if w.encoderEditor.text() == "":
		w.encoderEditor.setText('utf-8')
	return unicode( w.encoderEditor.text() )

def chardet():
	try:
		res = autoenc_multi( unicode( w.original.toPlainText() ) )
		w.encoderEditor.setText(res['encoder'])
		w.decoderEditor.setText(res['decoder'])
		w.converted.setPlainText( res['text'] )
		msg( 'encoder:%(encoder)s, decoder:%(decoder)s, chardet.encoding:%(auto)s, \
chardet.confidence:%(confidence)f, decoded text:%(text)s' % res )
	except:
		msgexc()

def convert():
	try:
		string = unicode( w.original.toPlainText() ).encode( typeEnc() )
		w.converted.setPlainText( string.decode( typeDec() ) )
		msg('Decode ok')
	except:
		msgexc()

### Items
### -------------------------------------------------------------

def closeItems():
	try:
		rows = set()
		for index in w.table.selectionModel().selectedIndexes():
			rows.add(index.row())
		for row in reversed(sorted(rows)):
			w.table.model().removeRows( row, 1 )
		msg( "Close ok" )
	except:
		error()

def writeItems():
	try:
		filenames = set()
		for index in w.table.selectionModel().selectedIndexes():
			qi = w.table.model().index( index.row(), 0 )
			filenames.add( unicode( w.table.model().data(qi) ) )
		fcount=0
		for filename in filenames:
			msg( 'Writing file %s' % filename )
			data = tagsdata[filename]
			for t, values in data['converted'].iteritems():
				for i, value in enumerate( values ):
					if value and isinstance( value, type( data['original'][t][i] ) ):
						data['original'][t][i] = value
			writeFile( filename )
			fcount +=1
		msg( 'Written %i file' % fcount )
	except:
		error()

def addItems(filenames):
	try:
		fcount=0
		for filename in filenames:
			print filename
			readFile( filename )
			msg( 'Reading file %s' % filename )
			fcount +=1
		msg( 'Readed %i file' % fcount )
		w.table.model()._update( tagsdata )
	except:
		error()

### synchronization --------
### ------------------------

possibility_map=[
('cp1252','cp1251'),
('cp1251','utf-8'),
('koi8-r', 'cp1251'),
('latin1', 'utf-8'),
('cp1251', 'utf-8'),
]

def fillPossib(index):
	try:
		possib = w.possib.model()
		possib.clear()
		possib.setHorizontalHeaderLabels( ['possibility'] )
		single = w.currentTable.model()
		qi = single.index( index.row(), single._hheadersR['original'] )
		value = single.data( qi )
		for e,d in possibility_map:
			try:
				item_text = unicode(value).encode(e).decode(d)+";e:"+e+";d:"+d+";"
				possib.appendRow( QStandardItem( item_text ) )
			except:
				pass
	except:
		error()

block_editorsToTable = False
def editorsToTable(text,field):
	try:
		global block_editorsToTable
		if block_editorsToTable:
			return
		global block_changedItemToEditors
		block_changedItemToEditors = True
		ci = w.currentTable.currentIndex()
		model = w.currentTable.model()
		i = model.index( ci.row(), model._hheadersR[field] )
		model.setData(i, QVariant(text) )
		block_changedItemToEditors = False
	except:
		error()

def convertedToTable():
	editorsToTable( w.converted.toPlainText(), 'converted' )

def encoderToTable( text ):
	editorsToTable( text, 'encoder' )

def decoderToTable( text ):
	editorsToTable( text, 'decoder' )

block_changedItemToEditors = False
def changedItemToEditors( tl, br ):
	try:
		if block_changedItemToEditors:
			return
		rowToEditors(w.currentTable.currentIndex())
	except:
		error()

def rowToEditors( index ):
	try:
		global block_editorsToTable
		block_editorsToTable = True
		model = w.currentTable.model()
		if index.isValid():
			_ie = model.index( index.row(), model._hheadersR['encoder'] )
			_id = model.index( index.row(), model._hheadersR['decoder'] )
			_io = model.index( index.row(), model._hheadersR['original'] )
			_ic = model.index( index.row(), model._hheadersR['converted'] )
			if model.data( _ie ):
				w.encoderEditor.setText( model.data( _ie ) )
			else:
				w.encoderEditor.clear()
			if model.data( _id ):
				w.decoderEditor.setText( model.data( _id ) )
			else:
				w.decoderEditor.clear()
			if model.data( _io ):
				w.original.setPlainText( model.data( _io ) )
			else:
				w.original.clear()
			if model.data( _ic ):
				w.converted.setPlainText( model.data( _ic ) )
			else:
				w.converted.clear()
		else:
			w.encoderEditor.clear()
			w.decoderEditor.clear()
			w.original.clear()
			w.converted.clear()
		block_editorsToTable = False
	except:
		error()

def multiCurrentToLabel(c):
	try:
		if c.isValid():
			qi = w.table.model().index( c.row(), 0 )
			w.currentLabel.setText( w.table.model().data( qi ) )
		else:
			w.currentLabel.setText( u'Nothing is selected' )
	except:
		error()

import sys, traceback
from tag import autoenc_multi, error

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

def init():
	from model import twoTables
	
	global app, w, two
	app = QApplication([])
	w = loadUi("ui.ui")
	
	two = twoTables( w.currentTable, w.table )
	
	#~ w.possib.setModel( QStandardItemModel() )
	
	#~ w.currentTable.selectionModel().currentChanged.connect( fillPossib )

	#~ w.converted.textChanged.connect( convertedToTable )
	#~ w.encoderEditor.textChanged.connect( encoderToTable )
	#~ w.decoderEditor.textChanged.connect( decoderToTable )
	#~ w.currentTable.model().dataChanged.connect( changedItemToEditors )
	#~ w.currentTable.selectionModel().currentChanged.connect( rowToEditors )
	#~ w.table.selectionModel().currentChanged.connect( multiCurrentToLabel )
	
	# Buttons
	#~ w.convertButton.clicked.connect(convert)
	#~ w.chardetButton.clicked.connect(chardet)
	#~ w.writeButton.clicked.connect( writeItems )
	#~ w.closeButton.clicked.connect( closeItems )
	#~ w.openButton.clicked.connect(openButton)

if __name__ == '__main__':
	from threading import Thread
	from time import sleep
	from PyQt4.QtCore import QThread
	from tag import getFileTags
	
	init()
	
	data = {}
	
	"""for filename in ( a.decode('utf-8') for a in sys.argv[1:] ):
		print filename
		data[filename]=getFileTags(filename)
	two.populateModel( data )"""
	
	from PyQt4.QtCore import QObject, pyqtSignal
	
	class loaderObject(QObject):
		msg = pyqtSignal(QString)
		loaded = pyqtSignal()
		def loadArgv(self):
			self.addItems( a.decode('utf-8') for a in sys.argv[1:] )
		def addItems(self, filenames):
			fcount=0
			for filename in filenames:
				print filename
				self.msg.emit( QString( 'Reading file %s' % filename ) )
				data[filename]=getFileTags(filename)
				fcount +=1
			self.msg.emit( QString( 'Readed %i file' % fcount ) )
			self.loaded.emit()
	
	loaderthread = QThread()
	loader = loaderObject()
	loader.moveToThread( loaderthread )
	loader.msg.connect( w.statusBar.showMessage )
	
	class emiterObject(QObject):
		signal = pyqtSignal()
		def populate(self):
			two.populateModel( data )
	emiter = emiterObject()
	emiter.signal.connect( loader.loadArgv )
	loader.loaded.connect( emiter.populate )
	
	loaderthread.start()
	
	w.show()
	emiter.signal.emit()
	app.exec_()
	loaderthread.exit()
