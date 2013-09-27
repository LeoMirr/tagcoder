#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# This is mp3 tag editor with convenient encode options

import sys, traceback
import tag
from PyQt4 import QtGui, QtCore, uic

# horizontalHeader for main table
# Note: Bacause of appendRow file must be execly 0
tableHH={'file':0,'confidence':1,
# For pytaglib
#'GENRE[0]':2,'ARTIST[0]':3,'ALBUM[0]':4,'TITLE[0]':5,'COMMENT[0]':6
# For tagpy
'genre[0]':2,'artist[0]':3,'album[0]':4,'title[0]':5,'comment[0]':6
}
# resolve currentTable's verticalHeaderItem to row number
currentVH={'title[2]':0}
# resolve currentTable's row number to ref { 'tag':0 }
currentVHref={0:['title',2]}
currentHH={'original':0,'converted':1,'chardet':2}

# Return headerItem number if exist, else create headerItem and return it number
# tag, index(not zero if there is multi value for tag),
# head(header map name->number), func(for creating headerItem)
def _pull(tag, index, head, headref, func):
	name = "%s[%i]"%(tag,index)
	if not head:
		head[name] = 0
	if name not in head:
		i = max( head.values() )
		head[name] = i + 1
		func( ( head[name], name ) )
	headref[ head[name] ] = [ tag, index ]
	return head[name]

def error():
	(type, val, tb) = sys.exc_info()
	traceback.print_tb( tb )
	print type, val
	w.statusBar.showMessage( u'%s %s' % (type, val) )
	for line in traceback.format_tb( tb ):
		e.text.appendPlainText( line )
	e.text.appendPlainText( u'%s %s' % (type, val) )
	e.show()

def printerr(string):
	print unicode(string)
	e.text.appendPlainText( unicode(string) )
	e.show()

### Current Table functions -----------------------
### -----------------------------------------------

def _currentPullRow(t,i):
	return _pull( t, i, currentVH, currentVHref, \
	lambda (i, n): current.setVerticalHeaderItem( i , QtGui.QStandardItem( n ) ) )

# pull column number by name in currentTable
def currentPullColumn( name ):
	if not currentHH:
		currentHH[name] = 0
	if not currentHH.has_key(name):
		i = max( currentHH.values() )
		currentHH[name] = i + 1
		current.setVerticalHeaderItem( currentHH[name] , QtGui.QStandardItem( name ) )
	return currentHH[name]

def currentIndexToReference(index,**a):
	if index.isValid() \
	and current.itemFromIndex(index) is not None:
		f = currentGetFile()
		( t, i ) = currentVHref[ index.row() ]
		j = unicode( current.horizontalHeaderItem( index.column() ).text() )
		#printerr( 'f:%s,j:%s,t:%s,i:%i;' % (f, j, t, i) )
		if 'f' in a:
			f=a['f']
		if 'j' in a:
			j=a['j']
		if 't' in a:
			t=a['t']
		if 'i' in a:
			i=a['i']
		return [ f, j, t, i ]

def currentGetValue(index,**a):
	r = currentIndexToReference(index,**a)
	if r:
		( f, j, t, i ) = r
		return tag.tagsdata[f][j][t][i]

def currentSetValue(index,value,**a):
	r = currentIndexToReference(index,**a)
	if r:
		( f, j, t, i ) = r
		tag.tagsdata[f]['converted'][t][i] = value
		(r,c) = ( ctSM.currentIndex().row(), ctSM.currentIndex().column() )
		currentRefresh()
		ctSM.setCurrentIndex( current.indexFromItem( current.item(r,c) )\
			, QtGui.QItemSelectionModel.Select )
		(r,c) = ( tSM.currentIndex().row(), tSM.currentIndex().column() )
		tableFillRow( tSM.currentIndex().row() )
		tSM.setCurrentIndex( table.indexFromItem( table.item(r,c) )\
			, QtGui.QItemSelectionModel.Select )

def currentClear():
	currentVH.clear()
	currentVHref.clear()
	current.clear()

def currentFill(filename):
	try:
		currentClear()
		for f in currentHH.keys():
			current.setHorizontalHeaderItem( currentHH[f] , QtGui.QStandardItem( f ) )
		data=tag.tagsdata[filename]
		for a in data.keys():
			for t, values in data[a].iteritems():
				for i, value in enumerate( values ):
					if a == "chardet":
						value = "c:%(confidence)f;a:%(auto)s;en:%(encoder)s;de:%(decoder)s" % value
					current.setItem( _currentPullRow(t,i), currentPullColumn(a), QtGui.QStandardItem(unicode(value)) )
		for f in currentVH.keys():
			current.setVerticalHeaderItem( currentVH[f] , QtGui.QStandardItem( f ) )
	except:
		error()

def currentGetFile():
	return unicode( w.currentLabel.text() )

def currentSetFile(filename):
	w.currentLabel.setText( filename )

def currentRefresh():
	if tSM.currentIndex().isValid:
		item = table.item( tSM.currentIndex().row(), 0 )
		if item is not None:
			filename = unicode( item.text() )
			currentSetFile(filename)
			currentFill( filename )
			return
	currentClear()
	currentSetFile("No file is selected.")

### Main Table funcions ---------------------------
### -----------------------------------------------

def tableGetCurrentFile():
	if tSM.currentIndex().isValid():
		i = table.item( tSM.currentIndex().row(), 0 )
		if i:
			return unicode( i.text() )
	return None

def _tablePullColumnT(t,i,y,x,cv):
	n = '%s[%i]' % (t,i)
	v = n
	x.setData( QtCore.QVariant( v ) )
	if n not in tableHH:
		n = 'other[%i]:' % y[0]
		y[0] += 1
		if n not in tableHH:
			tableHH[n] = max( tableHH.values() ) + 1
			table.setHorizontalHeaderItem( tableHH[n] , QtGui.QStandardItem( n ) )
	cv[v] = tableHH[n]
	return tableHH[n]

# pull column number by name in main table
def tablePullColumn(name):
	if not tableHH:
		tableHH[name] = 0
	if not tableHH.has_key(name):
		i = max( tableHH.values() )
		tableHH[name] = i + 1
		table.setHorizontalHeaderItem( tableHH[name] , QtGui.QStandardItem( name ) )
	return tableHH[name]

def tableFillRow(row):
	filename = unicode( table.item(row,0).text() )
	y=[0]
	cv = {}
	for t, values in tag.tagsdata[filename]['converted'].iteritems():
		for i, value in enumerate( values ):
			qi = QtGui.QStandardItem(value)
			table.setItem(row, _tablePullColumnT( t, i, y, qi, cv ), qi )
	chardet={'confidence':1.0, 'auto':'', 'decoder':'', 'encoder':''}
	for t, values in tag.tagsdata[filename]['chardet'].iteritems():
		for value in values:
			if value['auto'] == '':
				continue
			if value['confidence'] < chardet['confidence']:
				chardet = value
	table.setItem(row, tablePullColumn('confidence'), QtGui.QStandardItem(unicode(chardet['confidence'])) )
	table.item(row,0).setData( QtCore.QVariant( cv ) )

### Buttons ---------------------------------------
### -----------------------------------------------

def swapButton():
	string = unicode( w.text.toPlainText() )
	w.text.setPlainText( w.editor.toPlainText() )
	w.editor.setPlainText( string )

def setButton():
	try:
		index = ctSM.currentIndex()
		if index.isValid():
			currentSetValue( index, unicode( w.text.toPlainText() ), j='converted' )
		else:
			w.statusBar.showMessage( u'Nothing is selected' )
	except:
		error()

def getButton():
	try:
		index = ctSM.currentIndex()
		if index.isValid():
			a = unicode( currentGetValue( index, j='original' ) )
			b = unicode( currentGetValue( index, j='converted' ) )
			w.editor.setPlainText( a )
			w.text.setPlainText( b )
		else:
			w.statusBar.showMessage( u'Nothing is selected' )
	except:
		error()

def openButton(this):
	addItems( [ unicode( f ) for f in QtGui.QFileDialog.getOpenFileNames(w,u"open music files") ] )

def typeDec():
	if w.decoderEditor.text() == "":
		w.decoderEditor.setText('utf-8')
	return unicode( w.decoderEditor.text() )

def typeEnc():
	if w.encoderEditor.text() == "":
		w.encoderEditor.setText('utf-8')
	return unicode( w.encoderEditor.text() )

def codeOutput():
	if editMod():
		return w.text.setPlainText
	else:
		return lambda (string): ( currentSetValue( ctSM.currentIndex(), string, j='converted' )\
		,w.text.setPlainText(string) )

def autoButton():
	try:
		res = tag.autoenc_multi( unicode( w.editor.toPlainText() ) )
		w.encoderEditor.setText(res['encoder'])
		w.decoderEditor.setText(res['decoder'])
		codeOutput()( res['text'] )
		w.statusBar.showMessage( 'encoder:%(encoder)s, decoder:%(decoder)s, auto decoder:%(auto)s, \
confidence:%(confidence)f, decoded text:%(text)s' % res )
	except:
		error()

def decodeButton():
	try:
		string = unicode( w.editor.toPlainText() ).encode( typeEnc() )
		codeOutput()( string.decode( typeDec() ) )
	except:
		error()

def editMod():
	if w.editMod.isChecked():
		w.editor.setReadOnly(False)
	else:
		w.editor.setReadOnly(True)
	return w.editMod.isChecked()

def refreshDecode():
	if not editMod():
		getButton()

### Conversion between table and currentTable ----
### ----------------------------------------------

def currentIndexFromTable(index):
	if index.isValid():
		qi = table.itemFromIndex(index)
		if qi:
			qv = qi.data()
			if qv.isValid():
				name = unicode( qv.toString() )
				if name in currentVH:
					return current.indexFromItem( current.item( currentVH[name] , currentHH['converted'] ) )
	return QtCore.QModelIndex()

def tableIndexFromCurrent(index):
	if index.isValid():
		fi = table.item( tSM.currentIndex().row() , 0 )
		if fi:
			qv = fi.data()
			if qv.isValid():
				name = unicode( current.verticalHeaderItem( index.row() ).text() )
				if QtCore.QString(name) in qv.toPyObject():
					return table.indexFromItem( table.item( tSM.currentIndex().row() , qv.toPyObject()[QtCore.QString(name)] ) )
	return QtCore.QModelIndex()

def tSMc_func():
	try:
		if QtGui.QWidget.hasFocus(w.table):
			filename = tableGetCurrentFile()
			if filename != currentGetFile():
				currentRefresh()
			i = currentIndexFromTable( tSM.currentIndex() )
			if i.isValid():
				ctSM.clear()
				ctSM.setCurrentIndex( i, QtGui.QItemSelectionModel.Select )
	except:
		error()

def ctSMc_func():
	try:
		refreshDecode()
		if QtGui.QWidget.hasFocus(w.currentTable):
			filename = tableGetCurrentFile()
			if filename != currentGetFile():
				currentRefresh()
			i = tableIndexFromCurrent( ctSM.currentIndex() )
			if i.isValid():
				tSM.clear()
				tSM.setCurrentIndex( i, QtGui.QItemSelectionModel.Select )
	except:
		error()

### Functions that use table rows
### -------------------------------------------------------------

# if one or several indexes in lst is on the row, return number of that row
def indexesToRows(lst):
	rows={}
	for index in lst:
		if not rows.has_key( index.row() ):
			rows[ index.row() ]=None
	return rows.keys()

def tableColumnItems(rows, column=0):
	return [ table.item( row, column ) for row in rows ]

def itemsToValues(items):
	return [ unicode( item.text() ) for item in items ]

def readItems(rows):
	try:
		fcount = 0
		for row in rows:
			filename = unicode( table.item( row, 0 ).text() )
			w.statusBar.showMessage( u'Reading file %s' % filename )
			del tag.tagsdata[ filename ]
			tag.readFile(filename)
			tableFillRow( row )
			fcount += 1
		w.statusBar.showMessage( 'Readed %i file' % fcount )
		currentRefresh()
	except:
		error()

def closeItems(rows):
	try:
		rows.sort()
		rows.reverse()
		for row in rows:
			if tag.tagsdata.has_key( unicode( table.item(row, 0).text() ) ):
				del tag.tagsdata[ unicode( table.item(row, 0).text() ) ]
			table.removeRows( row,1)
		currentRefresh()
	except:
		error()

def writeItems(filenames):
	try:
		fcount=0
		for filename in filenames:
			w.statusBar.showMessage( 'Writing file %s' % filename )
			data = tag.tagsdata[filename]
			for t, values in data['converted'].iteritems():
				for i, value in enumerate( values ):
					if value and isinstance( value, type( data['original'][t][i] ) ):
						data['original'][t][i] = value
			tag.writeFile( filename )
			fcount +=1
		w.statusBar.showMessage( 'Written %i file' % fcount )
		currentRefresh()
	except:
		error()

def addItems(filenames):
	try:
		fcount=0
		for filename in filenames:
			tag.readFile( filename )
			item = QtGui.QStandardItem( filename )
			item.setEditable(False)
			table.appendRow( [ item ] )
			tableFillRow( table.indexFromItem( item ).row() )
			w.statusBar.showMessage( u'Reading file %s' % filename )
			fcount +=1
		w.statusBar.showMessage( 'Readed %i file' % fcount )
		currentRefresh()
	except:
		error()

if __name__ == '__main__':
	app = QtGui.QApplication([])

	w = uic.loadUi("ui.ui")
	e = uic.loadUi('error.ui')
	table = QtGui.QStandardItemModel()
	current = QtGui.QStandardItemModel()
	w.table.setModel( table )
	w.currentTable.setModel( current )
	tSM = w.table.selectionModel()
	ctSM = w.currentTable.selectionModel()

	for f in tableHH.keys():
		table.setHorizontalHeaderItem( tableHH[f] , QtGui.QStandardItem( f ) )

	# Buttons
	w.setButton.clicked.connect(setButton)
	w.getButton.clicked.connect(getButton)
	w.autoButton.clicked.connect(autoButton)
	w.decodeButton.clicked.connect(decodeButton)
	w.writeButton.clicked.connect( lambda : writeItems(itemsToValues(tableColumnItems(indexesToRows(tSM.selectedIndexes())))) )
	w.readButton.clicked.connect( lambda : readItems(indexesToRows(tSM.selectedIndexes())) )
	w.closeButton.clicked.connect( lambda : closeItems(indexesToRows(tSM.selectedIndexes())) )
	w.openButton.clicked.connect(openButton)
	w.swapButton.clicked.connect(swapButton)

	# Refresh
	tSM.selectionChanged.connect(tSMc_func)
	tSM.currentChanged.connect(tSMc_func)
	w.table.clicked.connect(tSMc_func)
	ctSM.currentChanged.connect(ctSMc_func)
	w.editMod.clicked.connect(refreshDecode)

	addItems( [ a.decode('utf-8') for a in sys.argv[1:] ] )

	editMod()
	w.show()

	sys.exit( app.exec_() )
