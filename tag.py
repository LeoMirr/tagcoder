#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
import tagpy
import tagpy.id3v1
import tagpy.id3v2
import sys, traceback, copy
from chardet.universaldetector import UniversalDetector
tagpy.id3v2.FrameFactory.instance().setDefaultTextEncoding(tagpy.StringType.UTF8)

import taglib

# tagsdata = { u'filename' : { 'original' : TAGS, 'converted' : TAGS, 'chardet' : CHARDET }, ... }
# TAGS = { 'tag1' : [ 'value1', ... ], ... }
# CHARDET = { 'tag1' : [ CHARDET_ITEM1, ... ], ... }
# CHARDET_ITEM = { 'text' : 'string', 'encoder' : 'string', 'decoder' : 'string', 'auto' : 'string', 'confidence' : 0.99 }
tagsdata={}

codeMap = {
'EUC-TW' : 'windows-1251',
'MacCyrillic' : 'windows-1251',
'TIS-620' : 'windows-1251',
'ISO-8859-5' : 'windows-1251',
'GB2312' : 'windows-1251'
}

def error():
	(type, val, tb) = sys.exc_info()
	traceback.print_exception(type, val, tb)

def codeReplace(code):
	if code in codeMap:
		return codeMap[code]
	return code

def autoenc_multi(text):
	res={'text': text, 'auto': '', 'encoder':'', 'decoder': '', 'confidence': 0.0}
	for encoder in ('latin1','cp1252','cp1251','cp1255'):
		new=autoenc(text, encoder=encoder)
		if res['confidence'] < new['confidence']:
			res=new
	return res

def autoenc(text,encoder="latin1"):
	res={'text': text, 'auto': '', 'encoder':'', 'decoder': '', 'confidence': 0.0}
	try:
		string=text.encode(encoder)
	except UnicodeEncodeError:
		#print 'encoder %s not get it' % (encoder)
		return res
	u=UniversalDetector()
	u.feed( string )
	u.close()
	if u.result['encoding'] == None:
		return res
	decoder=codeReplace( u.result['encoding'] )
	try:
		ustring=string.decode( decoder )
	except UnicodeDecodeError:
		#print 'decoder %s not get it' % (encoder)
		return res
	res={'text':ustring, 'auto':u.result['encoding'],
		'encoder':encoder, 'decoder':decoder, 'confidence':u.result['confidence'] }
	#print unicode( u'encoder:%(encoder)s, decoder:%(decoder)s, auto decoder:%(auto)s, \
#confidence:%(confidence)f, decoded text:%(text)s' % res ).encode('utf-8')
	return res

def decode(filename,text):
	res=autoenc(text)
	append=""
	if res['auto'] == "":
		return res
	if res['auto'] not in ( "windows-1251", "ascii", "utf-8" ):
		append = append + ", strange encoding " + res['auto']
	if res['auto'] != res['decoder']:
		append = append + ", " + res['auto'] + " change to " + res['decoder']
	if res['confidence'] < 0.8:
		append = append + ", confidence " + str( res['confidence'] )
	if append != "":
		a.append( filename.decode('utf-8') + append + ": " + res['text'] )
	return res

def parse(filename):
	#print filename + ":"
	#print "-" * 50
	f=tagpy.FileRef( filename )
	if f.isNull() == True:
		raise IOError("Can't open file")
	res={'genre':'','artist':'','album':'','title':'','comment':'','track':0,'year':0}
	res['genre'] = decode( filename , f.tag().genre )['text']
	res['artist'] = decode( filename , f.tag().artist )['text']
	res['album'] = decode( filename , f.tag().album )['text']
	res['title'] = decode( filename , f.tag().title )['text']
	res['comment'] = decode( filename , f.tag().comment )['text']
	res['track'] = f.tag().track
	res['year'] = f.tag().year
	#print "-" * 50
	return res

def getFileRef(filename):
	try:
		fileref = tagpy.FileRef( filename.encode('utf-8') )
	except ValueError as e:
		raise Exception('type',e)
	if fileref.isNull() == True:
		raise Exception('open',"Can't open file")
	return fileref

def getFileTags(filename):
	ref = getFileRef( filename )
	#t = ref.tag()
	fields = {}
	#fields['genre'] = [ t.genre ]
	#fields['artist'] = [ t.artist ]
	#fields['album'] = [ t.album ]
	#fields['title'] = [ t.title ]
	#fields['comment'] = [ t.comment ]
	#fields['track'] = [ t.track ]
	#fields['year'] = [ t.year ]
	_map = { 'TALB' : 'album',
	'COMM' : 'comment',
	'TRCK' : 'track',
	'TPE1' : 'artist',
	'TIT2' : 'title',
	'TCON' : 'genre'}
	ref.tag().duplicate(ref.file().ID3v1Tag(),ref.file().ID3v2Tag(),False)
	for v in ref.file().ID3v2Tag().frameList():
		if v.frameID() in _map:
			key = _map[ v.frameID() ]
		else:
			key = v.frameID()
		if key not in fields:
			fields[key] = []
		fields[key].append( v.toString() )
	return fields

def _getFileTags(filename):
	return copy.deepcopy( taglib.File( filename ).tags )

def setFileTags(filename, tags):
	ref = getFileRef( filename )
	t = ref.tag()
	(t.genre, \
	t.artist, \
	t.album, \
	t.title, \
	t.comment, \
	t.track, \
	t.year) = \
	( tags['genre'][0], \
	tags['artist'][0], \
	tags['album'][0], \
	tags['title'][0], \
	tags['comment'][0], \
	tags['track'][0], \
	tags['year'][0])
	ref.save()

def _setFileTags(filename, tags):
	ref = taglib.File(filename)
	for tag, values in tags.iteritems():
		for i, value in enumerate( values ):
			if tag in ref.tags and i < len(ref.tags[tag]):
				if value and isinstance( value, type(ref.tags[tag][i]) ):
					ref.tags[tag][i] = value
	for tag, values in ref.tags.iteritems():
		for i, value in enumerate( values ):
			print u"%s[%i] = \"%s\"" % ( tag, i, value )
	ref.save()

def writeFile(filename):
	setFileTags( filename, tagsdata[filename]['original'] )

def readFile(filename):
	original = getFileTags( filename )
	chardet = {}
	converted = {}
	for t, values in original.iteritems():
		chardet[t] = []
		converted[t] = []
		for value in values:
			if isinstance( value, type(u'string') ):
				auto = autoenc( value )
				chardet[t].append( auto )
				converted[t].append( auto['text'] )
	data = {filename:{ 'original' : original, 'converted' : converted, 'chardet' : chardet }}
	tagsdata.update(data)
	return data

if __name__ == '__main__':
	# for output
	a=[]
	tags={}
	for f in sys.argv[1:]:
		tags[f] = parse(f)

	print "\n".join(a)

	#print tags.viewitems()
