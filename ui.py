#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# This is mp3 tag editor with convenient encode options

import sys, traceback
import tag
import tagpy, tagpy.id3v1, tagpy.id3v2
from PyQt4 import QtGui, QtCore, uic

app = QtGui.QApplication([])

w = uic.loadUi("ui.ui")
e = uic.loadUi('error.ui')
items = QtGui.QStandardItemModel()
w.table.setModel( items )
bSm=w.table.selectionModel()

# Note: Bacause of appendRow file must be execly 0
head={'file':0,'genre':1,'artist':2,'album':3,'title':4,'comment':5,'track':6,'year':7,
'decoder':8,'encoder':9,'auto':10,'confidence':11}
for f in head.keys():
	items.setHorizontalHeaderItem( head[f] , QtGui.QStandardItem( f ) )

def swapDecode():
	string = unicode( w.text.toPlainText() )
	w.text.setPlainText( w.editor.toPlainText() )
	w.editor.setPlainText( string )
w.swapBtn.clicked.connect(swapDecode)

def error():
	(type, val, tb) = sys.exc_info()
	traceback.print_tb( tb )
	print type, val
	w.statusBar.showMessage( u'%s %s' % (type, val) )
	for line in traceback.format_tb( tb ):
		e.text.appendPlainText( line )
	e.text.appendPlainText( u'%s %s' % (type, val) )
	e.show()

def setItem():
	currentItem = items.item( bSm.currentIndex().row(), bSm.currentIndex().column() )
	currentItem.setText( w.editor.toPlainText() )
w.setBtn.clicked.connect(setItem)

def getItem():
	currentItem = items.item( bSm.currentIndex().row(), bSm.currentIndex().column() )
	w.editor.setPlainText( currentItem.text() )
w.getBtn.clicked.connect(getItem)

def typeDec():
	if w.decEdt.text() == "":
		w.decEdt.setText('utf-8')
	return unicode( w.decEdt.text() )

def typeEnc():
	if w.encEdt.text() == "":
		w.encEdt.setText('utf-8')
	return unicode( w.encEdt.text() )

def codeOutput():
	if editMod():
		return w.text
	else:
		return w.editor

def autodecode():
	try:
		res = tag.autoenc_multi( unicode( w.editor.toPlainText() ) )
		w.encEdt.setText(res['encoder'])
		w.decEdt.setText(res['decoder'])
		codeOutput().setPlainText( res['text'] )
		w.statusBar.showMessage( 'encoder:%(encoder)s, decoder:%(decoder)s, auto decoder:%(auto)s, \
confidence:%(confidence)f, decoded text:%(text)s' % res )
	except:
		error()
w.autodecBtn.clicked.connect(autodecode)

def decode():
	try:
		string = unicode( w.editor.toPlainText() ).encode( typeEnc() )
		codeOutput().setPlainText( string.decode( typeDec() ) )
	except:
		error()
w.decBtn.clicked.connect(decode)

def editMod():
	if w.editMod.isChecked():
		w.editor.setReadOnly(False)
	else:
		w.text.clear()
		w.editor.setReadOnly(True)
	return w.editMod.isChecked()

def decRefresh(this):
	if not editMod():
		getItem()
bSm.selectionChanged.connect(decRefresh)
bSm.currentChanged.connect(decRefresh)
w.table.clicked.connect(decRefresh)
w.editMod.clicked.connect(decRefresh)

def getSelected():
	sel=[]
	for index in bSm.selectedIndexes():
		if index.column() != head['file']:
			continue
		sel.append( index )
	return sel

def writeItems():
	try:
		fcount=0
		lst = getSelected()
		if len(lst) == 0:
			w.statusBar.showMessage( 'You must select one or more file, exacly first column' )
			return
		for index in lst:
			item = items.item( index.row(), index.column() )
			w.statusBar.showMessage( 'Writing file %s' % unicode( item.text() ) )
			ref = getFileRef( unicode( item.text() ).encode('utf-8') )
			fields={}
			for field in ("genre","artist","album","title","comment"):
				fields[field] = unicode( items.item( index.row(), head[field] ).text() )
			for field in ("year","track"):
				fields[field] = int( items.item( index.row(), head[field] ).text() )
			ref.tag().genre = fields["genre"]
			ref.tag().artist = fields['artist']
			ref.tag().album = fields['album']
			ref.tag().title = fields['title']
			ref.tag().comment = fields['comment']
			ref.tag().track = fields['track']
			ref.tag().year = fields['year']
			ref.save()
			fcount +=1
		w.statusBar.showMessage( 'Written %i file' % fcount )
	except:
		error()
w.nSb.clicked.connect(writeItems)

def getFileRef(filename):
	try:
		fileref = tagpy.FileRef( filename )
	except ValueError as e:
		raise Exception('type',e)
	if fileref.isNull() == True:
		raise Exception('open',"Can't open file")
	return fileref

def readItems():
	try:
		lst = getSelected()
		fcount=0
		if len(lst) == 0:
			w.statusBar.showMessage( 'You must select one or more file, exacly first column' )
			return
		for index in lst:
			item = items.item( index.row(), index.column() )
			t = getFileRef( unicode( item.text() ).encode('utf-8') ).tag()
			w.statusBar.showMessage( 'Reading file %s' % unicode( item.text() ) )
			fields = {}
			fields["genre"] = tag.autoenc( t.genre )
			fields['artist'] = tag.autoenc( t.artist )
			fields['album'] = tag.autoenc( t.album )
			fields['title'] = tag.autoenc( t.title )
			fields['comment'] = tag.autoenc( t.comment )
			fields['track'] = t.track
			fields['year'] = t.year
			columns={'confidence':1.0, 'auto':'', 'decoder':'', 'encoder':''}
			for field, value in fields.iteritems():
				if isinstance( value, type(int()) ):
					items.setItem(index.row(),head[field], QtGui.QStandardItem(str(value)) )
					continue
				if value['auto'] != '' and \
					value['confidence'] < columns['confidence']:
						columns = value
				items.setItem(index.row(),head[field], QtGui.QStandardItem(value['text']) )
			for column in ('confidence', 'auto', 'decoder', 'encoder'):
				items.setItem(index.row(),head[column], QtGui.QStandardItem( unicode( columns[column] ) ) )
			fcount +=1
		w.statusBar.showMessage( 'Readed %i file' % fcount )
	except:
		error()
w.nRb.clicked.connect(readItems)

def closeItems():
	sel=[]
	for index in bSm.selectedIndexes():
		if index.column() != head['file']:
			continue
		sel.append( index.row() )
	sel.sort()
	sel.reverse()
	for row in sel:
		items.removeRows( row,1)
w.nCb.clicked.connect(closeItems)

def openFiles(this):
	bSm.clear() # to prevent re-reading twice
	addItems( unicode( f ).encode('utf-8') for f in QtGui.QFileDialog.getOpenFileNames(w,u"open music files") )
	readItems()
	bSm.clear() # to prevent accidentally writing all opened files
w.nAb.clicked.connect(openFiles)

def addItems(filenames):
	for filename in filenames:
		item = QtGui.QStandardItem( filename.decode('utf-8') )
		item.setEditable(False)
		items.appendRow( [ item ] )
		bSm.select( item.index(), QtGui.QItemSelectionModel.Select )

if __name__ == '__main__':
	bSm.clear()
	addItems(sys.argv[1:])
	readItems()
	bSm.clear()

	editMod()
	w.show()

	sys.exit( app.exec_() )
