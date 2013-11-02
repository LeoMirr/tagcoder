#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
# Name: model
# Description: Model for view

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys, inspect

def populateModel( model, data ):
	for filename, tags in data.iteritems():
		fileKeyItem = QStandardItem( QString(filename) )
		fileValueItem = QStandardItem( QString( str(len(tags)) ) )
		for tag, values in tags.iteritems():
			tagKeyItem = QStandardItem( QString( tag ) )
			tagValueItem = QStandardItem( QString( str(len(values)) ) )
			for num, value in enumerate(values):
				chardet = autoenc( unicode( value ) )
				trow = []
				trow.append( QStandardItem( QString( str(num) ) ) )
				trow.append( QStandardItem(value) )
				trow.append( QStandardItem( chardet['text'] ) )
				trow.append( QStandardItem( str( chardet['confidence'] ) ) )
				tagKeyItem.appendRow( trow )
			fileKeyItem.appendRow( [tagKeyItem, tagValueItem] )
		model.appendRow( [ fileKeyItem, fileValueItem ] )

if __name__ == '__main__':
	from PyQt4.uic import loadUi
	from tag import getFileTags, error, autoenc
	import traceback, sys
	
	app = QApplication([])
	w = loadUi("tree.ui")
	
	data = {}
	for _filename in sys.argv[1:]:
		filename = _filename.decode('utf-8')
		print filename
		data[filename]=getFileTags(filename)
	
	model = QStandardItemModel()
	
	populateModel( model, data )
	
	w.treeView.setModel(model)
	w.tableView.setModel(model)
	
	w.treeView.selectionModel().currentChanged.connect( lambda a: a.column() == 0 and w.tableView.setRootIndex(a) )
	
	w.show()
	app.exec_()
