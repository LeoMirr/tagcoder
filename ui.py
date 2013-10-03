#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Name: tagcoder
# Description: This is mp3 tag editor with convenient encode options

def error():
	(type, val, tb) = sys.exc_info()
	traceback.print_exception(type, val, tb)
	msg( ''.join( traceback.format_exception_only(type,val) ) )
	e.text.appendPlainText( ''.join( traceback.format_exception(type, val, tb) ) )
	e.show()

def printerr(string):
	sys.stderr.write( unicode(string) + u"\n" )
	e.text.appendPlainText( unicode(string) )
	e.show()

def msg(m):
	w.statusBar.showMessage( unicode( m ) )

def msgexc():
	(type, val, tb) = sys.exc_info()
	traceback.print_exception(type, val, tb)
	msg( ''.join( traceback.format_exception_only(type,val) ) )

def expect(strings, func = lambda : False ):
	(type, val, tb) = sys.exc_info()
	curr = ''.join( traceback.format_exception_only(type,val) )
	if curr in strings:
		msg(curr)
		return strings[curr]()
	else:
		return func()

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

### Functions that use table rows
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
			w.table.model()._update( readFile( filename ) )
			msg( 'Reading file %s' % filename )
			fcount +=1
		msg( 'Readed %i file' % fcount )
	except:
		error()

### synchronization --------
### ------------------------

def convertedToTable():
	try:
		global block_changedItemToEditors
		block_changedItemToEditors = True
		ci = w.currentTable.currentIndex()
		model = w.currentTable.model()
		i = model.index( ci.row(), model._hheadersR['converted'] )
		model.setData(i, QVariant( w.converted.toPlainText() ) )
		block_changedItemToEditors = False
	except:
		error()

def encoderToTable( text ):
	try:
		w.encoderEditor.blockSignals(True)
		ci = w.currentTable.currentIndex()
		model = w.currentTable.model()
		i = model.index( ci.row(), model._hheadersR['encoder'] )
		model.setData(i, QVariant(text) )
		w.encoderEditor.blockSignals(False)
	except:
		error()

def decoderToTable( text ):
	try:
		w.decoderEditor.blockSignals(True)
		ci = w.currentTable.currentIndex()
		model = w.currentTable.model()
		i = model.index( ci.row(), model._hheadersR['decoder'] )
		model.setData(i, QVariant(text) )
		w.decoderEditor.blockSignals(False)
	except:
		error()

block_changedItemToEditors = False
def changedItemToEditors( tl, br ):
	try:
		if block_changedItemToEditors:
			return
		if tl.isValid()\
		and tl == br:
			rowToEditors(tl)
	except:
		error()

def rowToEditors( index ):
	try:
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
from tag import readFile, tagsdata, autoenc_multi, writeFile

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

def init():

	from _model import singleModel, multiModel, singleSelectionToMulti,\
		multiSelectionToSingle, multiUpdate, singleUpdate
	
	global app, w, e
	app = QApplication([])
	w = loadUi("ui.ui")
	e = loadUi('error.ui')
	
	import _model
	
	_model.w = w
	
	w.currentTable.setModel( singleModel( tagsdata ) )
	w.table.setModel( multiModel( tagsdata ) )

	# connect
	w.currentTable.model().dataChanged.connect(multiUpdate)
	w.currentTable.selectionModel().currentChanged.connect(singleSelectionToMulti)
	w.table.model().dataChanged.connect(singleUpdate)
	w.table.selectionModel().currentChanged.connect(multiSelectionToSingle)
	
	w.converted.textChanged.connect( convertedToTable )
	w.encoderEditor.textChanged.connect( encoderToTable )
	w.decoderEditor.textChanged.connect( decoderToTable )
	w.currentTable.model().dataChanged.connect( changedItemToEditors )
	w.currentTable.selectionModel().currentChanged.connect( rowToEditors )
	w.table.selectionModel().currentChanged.connect( multiCurrentToLabel )
	
	# Buttons
	w.convertButton.clicked.connect(convert)
	w.chardetButton.clicked.connect(chardet)
	w.writeButton.clicked.connect( writeItems )
	w.closeButton.clicked.connect( closeItems )
	w.openButton.clicked.connect(openButton)

	addItems( [ a.decode('utf-8') for a in sys.argv[1:] ] )

	#editMod()

if __name__ == '__main__':
	init()
	w.show()
	app.exec_()
