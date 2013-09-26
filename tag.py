#!/usr/bin/python2
# vim: set fileencoding=utf-8 :
import tagpy
import tagpy.id3v1
import tagpy.id3v2
import sys, traceback
from chardet.universaldetector import UniversalDetector
tagpy.id3v2.FrameFactory.instance().setDefaultTextEncoding(tagpy.StringType.UTF8)

# for output
global a
a=[]

def error():
	(type, val, tb) = sys.exc_info()
	traceback.print_tb( tb )
	print type, val

codeMap = {
'EUC-TW' : 'windows-1251',
'MacCyrillic' : 'windows-1251',
'TIS-620' : 'windows-1251',
'ISO-8859-5' : 'windows-1251',
'GB2312' : 'windows-1251'
}

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
		print 'encoder %s not get it' % (encoder)
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
		print 'decoder %s not get it' % (encoder)
		return res
	res={'text':ustring, 'auto':u.result['encoding'],
		'encoder':encoder, 'decoder':decoder, 'confidence':u.result['confidence'] }
	print unicode( u'encoder:%(encoder)s, decoder:%(decoder)s, auto decoder:%(auto)s, \
confidence:%(confidence)f, decoded text:%(text)s' % res ).encode('utf-8')
	return res

def decode(filename,text):
	res=autoenc(text)
	append=""
	if res['auto'] == "":
		return res
	if ( res['auto'] != "windows-1251" ) and\
		(res['auto'] != "ascii" ):
		append = append + ", strange encoding " + res['auto']
	if res['auto'] != res['decoder']:
		append = append + ", " + res['auto'] + " change to " + res['decoder']
	if res['confidence'] < 0.8:
		append = append + ", confidence " + str( res['confidence'] )
	if append != "":
		a.append( filename.decode('utf-8') + append + ": " + res['text'] )
	return res

def parse(filename):
	print filename + ":"
	print "-" * 50
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
	print "-" * 50
	return res

if __name__ == '__main__':
	tags={}
	for f in sys.argv[1:]:
		tags[f] = parse(f)

	for n in a[:]:
		print n

	#print tags.viewitems()
