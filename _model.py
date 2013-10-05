#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Name: model
# Description: seamless synchronization of model and data

from PyQt4.QtCore import QAbstractItemModel, Qt, QString, QModelIndex, QVariant
from PyQt4.QtGui import QItemSelectionModel

class multiModel(QAbstractItemModel):
	def __init__(self, data, parent = None):
		QAbstractItemModel.__init__(self, parent)
		self._data = data
		self._table = []
		self._tableR = {}
		self._headers = ['file','confidence']
		self._headersR = { v:i for i,v in enumerate(self._headers) }
		self._update(self._data)
	
	def _tagColumn(self, t, i, v):
		header = '%s[%i]' % (t,i)
		if header in self._headersR:
			return self._headersR[header]
		other = 'some tag #%i' % v[0]
		v[0] += 1
		if other not in self._headersR:
			column = len( self._headers )
			self.beginInsertColumns(QModelIndex(), column, column)
			self._headersR[other] = column
			self._headers.append(other)
			self.endInsertColumns()
		return self._headersR[other]
	
	def _update(self, _data):
		self.modelAboutToBeReset.emit()
		for filename, data in _data.iteritems():
			v = [0]
			if filename not in self._tableR:
				row = self.rowCount()
				self.beginInsertRows(QModelIndex(), row, row)
				self._table.append( {'filename':filename,'t2c':{},0:filename,1:1.0} )
				self._tableR[filename] = row
				self.endInsertRows()
			row = self._tableR[filename]
			for j, tags in data.iteritems():
				for t, values in tags.iteritems():
					for i, value in enumerate( values ):
						if j == 'chardet':
							if value['auto']\
							and value['confidence'] < self._table[row][1]:
								self._table[row][1] = value['confidence']
							continue
						if j == 'converted':
							column = self._tagColumn( t, i, v )
							self._table[row][column]=(t,i)
							self._table[row]['t2c'][(t,i)]=column
		self.modelReset.emit()
		self.dataChanged.emit(QModelIndex(),QModelIndex())
	
	def _file( self, index ):
		return self._table[ index.row() ]['filename']
	
	def _ref( self, row, column ):
		f = self._table[row]['filename']
		if column in self._table[row]:
			h = self._table[row][column]
			if isinstance( h, type( () ) ):
				(t,i) = h
				j = 'converted'
				return [f,j,t,i]
		return None
	
	def _span(self, ref ):
		(f,j,t,i) = ref[0:4]
		if j != 'converted':
			return None
		try:
			row = self._tableR[f]
			column = self._table[row]['t2c'][(t,i)]
			return (row,column)
		except:
			return None
	
	def sort(self, column, order = Qt.AscendingOrder ):
		def _key(row):
			if column in row:
				if isinstance( row[column], type( () ) ):
					(t,i)=row[column]
					f = row['filename']
					j = 'converted'
					return self._data[f][j][t][i]
				else:
					return row[column]
			else:
				return u''
		self.layoutAboutToBeChanged.emit()
		_sorted = sorted(self._table, key=_key, reverse=order )
		self._table = _sorted
		self._tableR = { self._table[row]['filename']:row for row in range(len(self._table)) }
		self.layoutChanged.emit()
	
	def index( self, row, column, parent = QModelIndex() ):
		#return self.createIndex( row, column, self )
		return self.createIndex( row, column, None )
	
	def data( self, index, role = Qt.DisplayRole ):
		if index.isValid()\
		and role in (Qt.DisplayRole, Qt.EditRole):
			if index.column() in (0,1):
				value = self._table[index.row()][index.column()]
			else:
				#ref = index.internalPointer()._ref(index.row(),index.column())
				ref = self._ref(index.row(),index.column())
				if not ref:
					return
				(f,j,t,i) = ref
				value = self._data[f][j][t][i]
			return QString( unicode(value) )
	
	def setData(self, index, value, role = Qt.EditRole):
		if index.isValid()\
		and role == Qt.EditRole:
			#ref = index.internalPointer()._ref(index.row(),index.column())
			ref = self._ref(index.row(),index.column())
			if not ref:
				return False
			(f,j,t,i) = ref
			g = self._data[f][j][t]
			g[i] = type( g[i] )( unicode(value.toString()) )
			self.dataChanged.emit( index, index )
			return True
		return False
	
	def headerData( self, section, orientation, role = Qt.DisplayRole ):
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return QString(self._headers[section])
			if orientation == Qt.Vertical:
				return QString( unicode( section + 1 ) )
	
	def parent( self, index ):
		return QModelIndex()
	
	def removeRows(self, row, count, parent = QModelIndex() ):
		self.beginRemoveRows(QModelIndex(), row, row+count-1)
		for i in range( row, row+count ):
			filename = self._table[i]['filename']
			del self._tableR[ filename ]
			del self._table[i]
			del self._data[ filename ]
		self.endRemoveRows()
	
	def rowCount( self, parent = QModelIndex() ):
		if not parent.isValid():
			return len(self._table)
	
	def columnCount( self, parent = QModelIndex() ):
		if not parent.isValid():
			return len(self._headers)
	
	def flags( self, index ):
		_flags = Qt.ItemIsSelectable|Qt.ItemIsEnabled
		if index.isValid() \
		and index.column() in self._table[index.row()]:
			if isinstance(self._table[index.row()][index.column()],type( () )):
				_flags = _flags | Qt.ItemIsEditable
		return _flags

class singleModel(QAbstractItemModel):
	def __init__(self, data, filename=None, parent = None ):
		QAbstractItemModel.__init__(self, parent)
		self._data = data
		self._file = filename
		self._hheaders = ['original', 'converted', 'encoder', 'decoder', 'chardet']
		self._hheadersR = { v:i for i,v in enumerate(self._hheaders) }
		self._table = []
		self._tableR = {}
		if filename:
			self._update()
	
	def _tagRow(self, t,i):
		if (t,i) not in self._tableR:
			row = len(self._table)
			self._tableR[(t,i)] = row
			self._table.append( (t,i) )
		return self._tableR[(t,i)]
	
	def _update(self):
		for j, tags in self._data[self._file].iteritems():
			for t, values in tags.iteritems():
				for i, value in enumerate( values ):
					self._tagRow(t,i)
	
	def _toFile(self, filename ):
		self.modelAboutToBeReset.emit()
		_new = type(self)(self._data, filename=filename)
		for attr in ('_file','_hheaders','_hheadersR','_table','_tableR'):
			setattr( self, attr, getattr( _new, attr ) )
		print self._table
		self.modelReset.emit()
	
	def _ref(self, row, column):
		f = self._file
		(t,i) = self._table[row]
		columnName = self._hheaders[column]
		if columnName in ( 'original', 'converted', 'chardet' ):
			j = columnName
			try:
				self._data[f][j][t][i]
			except:
				return None
			return (f,j,t,i)
		if columnName in ( 'encoder', 'decoder' ):
			j = 'chardet'
			k = columnName
			try:
				self._data[f][j][t][i][k]
			except:
				return None
			return (f,j,t,i,k)
	
	def _span(self, ref ):
		if ref[0] != self._file:
			return None
		if len(ref) == 4:
			(f,j,t,i) = ref
			row = self._tableR[(t,i)]
			column = self._hheadersR[j]
		if len(ref) == 5:
			(f,j,t,i,k) = ref
			if k not in ('decoder', 'encoder'):
				return None
			row = self._tableR[(t,i)]
			column = self._hheadersR[k]
		return (row,column)
	
	def _get(self, ref):
		if len(ref) == 4:
			(f,j,t,i) = ref
			return self._data[f][j][t][i]
		if len(ref) == 5:
			(f,j,t,i,k) = ref
			return self._data[f][j][t][i][k]
	
	def _set(self, ref, value):
		if len(ref) == 4:
			(f,j,t,i) = ref
			self._data[f][j][t][i] = value
		if len(ref) == 5:
			(f,j,t,i,k) = ref
			self._data[f][j][t][i][k] = value
	
	def clear(self):
		self.modelAboutToBeReset.emit()
		self._file = ''
		self._table = []
		self._tableR = {}
		self.modelReset.emit()
	
	def parent( self, index ):
		return QModelIndex()
	
	def columnCount(self, parent = None):
		return len(self._hheaders)
	
	def rowCount(self, parent = None):
		return len(self._table)
	
	def index(self, row, column, parent = QModelIndex() ):
		#return self.createIndex( row, column, self )
		return self.createIndex( row, column, None )
	
	def data( self, index, role = Qt.DisplayRole ):
		if index.isValid()\
		and role in (Qt.DisplayRole,Qt.EditRole):
			#ref = index.internalPointer()._ref(index.row(),index.column())
			ref = self._ref(index.row(),index.column())
			if not ref:
				return
			value = self._get(ref)
			if isinstance( value, type( {} ) ):
				value = 'c:%(confidence)f; a:%(auto)s;' % value
			return QString( unicode( value ) )
	
	def setData(self, index, value, role = Qt.EditRole):
		if role == Qt.EditRole\
		and index.isValid():
			#ref = index.internalPointer()._ref(index.row(),index.column())
			ref = self._ref(index.row(),index.column())
			if not ref:
				return False
			self._set( ref, type( self._get(ref) )( unicode( value.toString() ) ) )
			self.dataChanged.emit( index, index )
			return True
		return False
	
	def headerData( self, section, orientation, role = Qt.DisplayRole ):
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return QString(self._hheaders[section])
			if orientation == Qt.Vertical:
				return QString('%s[%i]'%self._table[section])
	
	def flags(self, index):
		_flags = Qt.ItemIsSelectable|Qt.ItemIsEnabled
		#ref = index.internalPointer()._ref(index.row(),index.column())
		ref = self._ref(index.row(),index.column())
		if ref:
			if ref[1] == 'converted'\
			or len(ref) == 5:
				_flags = _flags | Qt.ItemIsEditable
		return _flags

blockSelectionTo = False
def singleSelectionToMulti(c):
	global blockSelectionTo
	if blockSelectionTo:
		return
	blockSelectionTo = True
	try:
		single = w.currentTable.model()
		multi = w.table.model()
		ref = single._ref( c.row(), c.column() )
		if ref:
			(f,j,t,i) = ref[0:4]
			j = 'converted'
			rc = multi._span( (f,j,t,i) )
			if rc:
				w.table.setCurrentIndex( multi.index(*rc) )
	except:
		error()
	blockSelectionTo = False

def multiSelectionToSingle(c):
	global blockSelectionTo
	if blockSelectionTo:
		return
	single = w.currentTable.model()
	multi = w.table.model()
	blockSelectionTo = True
	try:
		if c.isValid():
			if multi._file(c) != single._file:
				single._toFile( multi._file(c) )
			ref = multi._ref( c.row(), c.column() )
			if ref:
				rc = single._span(ref)
				if rc:
					w.currentTable.setCurrentIndex( multi.index(*rc) )
			else:
				w.currentTable.selectionModel().clearSelection()
				w.currentTable.selectionModel().currentChanged.emit(QModelIndex(),QModelIndex())
		else:
			single.clear()
	except:
		error()
	blockSelectionTo = False

def multiUpdate():
	w.currentTable.model().blockSignals(True)
	w.table.model().dataChanged.emit(QModelIndex(),QModelIndex())
	w.currentTable.model().blockSignals(False)

def singleUpdate():
	w.table.model().blockSignals(True)
	w.currentTable.model().dataChanged.emit(QModelIndex(),QModelIndex())
	w.table.model().blockSignals(False)

from tag import error

def init():
	from PyQt4.QtGui import QApplication, QSortFilterProxyModel
	from PyQt4.uic import loadUi
	from ui import error, msgexc, printerr
	import ui
	import traceback, sys
	from tag import readFile, tagsdata, error

	global app, w, e
	
	app = QApplication([])
	w = loadUi("ui.ui")
	e = loadUi('error.ui')
	
	global single
	#readFile('tmp/exemple.mp3')
	#single = singleModel( tagsdata, 'tmp/exemple.mp3' )
	#proxy = QSortFilterProxyModel()
	#proxy.setSourceModel( single )
	w.currentTable.setModel( singleModel(tagsdata) )
	#w.currentTable.setSortingEnabled( True )
	w.table.setModel(multiModel(tagsdata) )

	# connects
	w.currentTable.model().dataChanged.connect(multiUpdate)
	w.currentTable.selectionModel().currentChanged.connect(singleSelectionToMulti)
	w.table.model().dataChanged.connect(singleUpdate)
	w.table.selectionModel().currentChanged.connect(multiSelectionToSingle)
	
	ui.e = e
	ui.w = w

	readFile('tmp/exemple.mp3')
	readFile('tmp/exemple_id3v2_utf8.mp3')
	w.currentTable.model()._toFile('tmp/exemple.mp3')
	w.table.model()._update(tagsdata)

if __name__ == '__main__':
	init()
	w.show()
	app.exec_()
	print 'End'
