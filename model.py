#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Name: model
# Description: Model for view

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class twoTables(object):
	def __init__(self, singleTable, multiTable):
		self.single = singleTable
		self.multi = multiTable
		self.file2row = {}
		
		multimodel = QStandardItemModel()
		singlemodel = QStandardItemModel()
		
		multimodel.itemChanged.connect( self.fillSingleItemFromMulti )
		singlemodel.itemChanged.connect( self.fillMultiItemFromSingle )
		
		proxy = QSortFilterProxyModel()
		proxy.setSourceModel( multimodel )
		
		self.multi.setModel(proxy)
		self.single.setModel(singlemodel)
		
		self.multi.selectionModel().currentChanged.connect( self.selectSingleFromMulti )
		self.single.selectionModel().currentChanged.connect( self.selectMultiFromSingle )
	
	def populateModel( self, data ):
		single = self.single.model()
		for filename, tags in data.iteritems():
			fileItem = QStandardItem( QString(filename) )
			if filename in self.file2row:
				single.setItem( self.file2row[filename], 0, fileItem )
			else:
				single.appendRow( [ fileItem ] )
				self.file2row[filename] = fileItem.row()
			row = fileItem.row()
			for tag, values in tags.iteritems():
				for num, value in enumerate(values):
					key = QStandardItem( '%s[%i]' % (tag,num) )
					key.setData( QVariant( (tag,num) ) )
					orig = QStandardItem(value)
					chardet = autoenc( unicode( value ) )
					conv = QStandardItem( chardet['text'] )
					cnfd = QStandardItem( unicode( chardet['confidence'] ) )
					fileItem.appendRow( [key,orig,conv,cnfd] )
			self.updataRow( row )
			#~ self.updateParentRow( fileItem )
		single.setHorizontalHeaderLabels( [ 'key', 'original', 'converted', 'confidence' ] )
		self.multi.selectionModel().setCurrentIndex( self.multi.model().index(0,0)\
		, QItemSelectionModel.ClearAndSelect )
	
	def updateParentRow( self, parentItem ):
		single = self.single.model()
		rowToProp = []
		for _row in range( parentItem.rowCount() ):
			rowToProp.append( (\
				unicode( parentItem.child( _row, 2 ).text() ),
				float( parentItem.child( _row, 3 ).text() ) ) )
		_min = 1.0
		if len(rowToProp):
			_min = min( [ ( v[1] or 1.0 ) for v in rowToProp ] )
		columnToRow = sorted(range(len(rowToProp)), key=lambda i: rowToProp[i][1] or 1.0 )
		rowToColumn = range(len(columnToRow))
		for i, v in enumerate(columnToRow):
			rowToColumn[v]=i
		parentItem.setData( QVariant( rowToColumn ) )
		row = parentItem.row()
		single.setItem( row, 1, QStandardItem( unicode( _min ) ) )
		for c, r in enumerate(columnToRow):
			qit = QStandardItem( unicode( rowToProp[r][0] ) )
			qit.setData( QVariant( r ) )
			single.setItem( row, c+2, qit )
	
	def updataHeader( self ):
		multi = self.multi.model().sourceModel()
		multi.setHorizontalHeaderLabels( ['file','confidence']\
			+[ 'tag #%i'%i for i in range(multi.columnCount()-2) ] )
	
	def updataRow( self, row ):
		single = self.single.model()
		multi = self.multi.model().sourceModel()
		fileItem = single.item( row, 0 )
		rowToProp = []
		for _row in range( fileItem.rowCount() ):
			rowToProp.append( (\
				unicode( fileItem.child( _row, 2 ).text() ),
				float( fileItem.child( _row, 3 ).text() ) ) )
		_min = 1.0
		if len(rowToProp):
			_min = min( [ ( v[1] or 1.0 ) for v in rowToProp ] )
		columnToRow = sorted(range(len(rowToProp)), key=lambda i: rowToProp[i][1] or 1.0 )
		rowToColumn = range(len(columnToRow))
		for i, v in enumerate(columnToRow):
			rowToColumn[v]=i
		targetFileItem = QStandardItem( fileItem.text() )
		targetFileItem.setData( QVariant( rowToColumn ) )
		multi.setItem( row, 0, targetFileItem )
		multi.setItem( row, 1, QStandardItem( unicode( _min ) ) )
		for c, r in enumerate(columnToRow):
			qit = QStandardItem( unicode( rowToProp[r][0] ) )
			qit.setData( QVariant( r ) )
			multi.setItem( row, c+2, qit )
		self.updataHeader()
	
	def scrapData( self, row ):
		model = self.single.model()
		fileItem = model.item( row, 0 )
		fields = {}
		for _row in range( fileItem.rowCount() ):
			(t,i) = fileItem.child( _row, 0 ).data(Qt.UserRole + 1).toPyObject()
			fields.setdefault( t, {} )
			fields[t][i] = unicode( fileItem.child( _row, 2 ).text() )
		for t in fields.keys():
			values = range(len(fields[t]))
			for k, v in fields[t].items():
				values[k]=v
			fields[t]=values
		return fields
	
	def singleIndexFromMulti( self, multiIndex ):
		singlemodel = self.single.model()
		singleFileIndex = singlemodel.index( multiIndex.row(), 0 )
		if multiIndex.column() > 1:
			row = multiIndex.data(Qt.UserRole + 1).toPyObject()
			if row is not None:
				return singlemodel.index( row, 2, singleFileIndex )
		return QModelIndex()
	
	def multiIndexFromSingle( self, singleIndex ):
		multimodel = self.multi.model().sourceModel()
		row = self.single.model().parent( singleIndex ).row()
		rowToColumn = multimodel.index( row, 0 ).data(Qt.UserRole + 1).toPyObject()
		if rowToColumn is not None:
			column = rowToColumn[ singleIndex.row() ] + 2
			return multimodel.index( row, column )
		return QModelIndex()
	
	block_fillSingleItemFromMulti = False
	def fillSingleItemFromMulti( self, item ):
		if not item:
			return
		if self.block_fillSingleItemFromMulti:
			return
		self.block_fillMultiItemFromSingle = True
		singleIndex = self.singleIndexFromMulti( item.index() )
		if singleIndex.isValid():
			self.single.model().itemFromIndex( singleIndex ).setText( item.text() )
		self.block_fillMultiItemFromSingle = False
	
	block_fillMultiItemFromSingle = False
	def fillMultiItemFromSingle( self, item ):
		if not item:
			return
		if self.block_fillMultiItemFromSingle:
			return
		self.block_fillSingleItemFromMulti = True
		multiIndex = self.multiIndexFromSingle( item.index() )
		if multiIndex.isValid():
			self.multi.model().sourceModel().itemFromIndex( multiIndex ).setText( item.text() )
		self.block_fillSingleItemFromMulti = False
	
	block_selectMultiFromSingle = False
	def selectMultiFromSingle( self, singleIndex ):
		try:
			if self.block_selectMultiFromSingle:
				return
			self.block_selectSingleFromMulti = True
			multimodel = self.multi.model().sourceModel()
			singleFileIndex = self.single.model().parent( singleIndex )
			row = singleFileIndex.row()
			multiFileIndex = multimodel.index( row, 0 )
			data = multiFileIndex.data(Qt.UserRole + 1)
			rowToColumn = data.toPyObject()
			if rowToColumn is not None:
				column = rowToColumn[ singleIndex.row() ] + 2
				multiIndex = multimodel.index( row, column )
				proxyIndex = self.multi.model().mapFromSource( multiIndex )
				self.multi.setCurrentIndex( proxyIndex )
			self.block_selectSingleFromMulti = False
		except:
			error()
	
	block_selectSingleFromMulti = False
	def selectSingleFromMulti( self, proxyIndex ):
		try:
			if self.block_selectSingleFromMulti:
				return
			self.block_selectMultiFromSingle = True
			singlemodel = self.single.model()
			multiIndex = self.multi.model().mapToSource( proxyIndex )
			singleFileIndex = singlemodel.index( multiIndex.row(), 0 )
			self.single.setRootIndex( singleFileIndex )
			if multiIndex.column() > 1:
				row = multiIndex.data(Qt.UserRole + 1).toPyObject()
				if row is not None:
					self.single.setCurrentIndex( \
						singlemodel.index( row, 2, singleFileIndex ) )
			self.block_selectMultiFromSingle = False
		except:
			error()

class headerProxy(QAbstractItemModel):
	"""Make Vertical headers from 1st column and 
Horizontal headers from 1st row"""
	pass

from tag import error, autoenc

if __name__ == '__main__':
	from PyQt4.uic import loadUi
	from tag import getFileTags
	import traceback, sys
	
	app = QApplication([])
	w = loadUi("ui.ui")
	
	two = twoTables( w.currentTable, w.table )
	
	data = {}
	for _filename in sys.argv[1:]:
		filename = _filename.decode('utf-8')
		print filename
		data[filename]=getFileTags(filename)
	
	two.populateModel( data )
	
	#sys.exit()
	for t,vs in two.scrapData( 0 ).iteritems():
		for i, v in enumerate( vs ):
			print t,i,v
	
	
	w.show()
	app.exec_()
