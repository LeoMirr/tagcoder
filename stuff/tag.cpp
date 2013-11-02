#include <taglib/fileref.h>
#include <taglib/mpegfile.h>
#include <taglib/id3v1tag.h>
#include <taglib/id3v2tag.h>
#include <taglib/tbytevector.h>
#include <taglib/attachedpictureframe.h>
#include <stdio.h>
#include <typeinfo>
#include <iostream>
#include <fstream>
int main(int argc,char **argv){
	if( argc == 1 ){
		printf("You must specify one at least one argumet\n");
		return 1;
	}
	TagLib::FileRef file( argv[1] );
	if( file.isNull() ){
		printf("Can't open file %s\n",argv[1]);
		return 1;
	}
	
	TagLib::MPEG::File* mpeg = dynamic_cast<TagLib::MPEG::File*>( file.file() );
	
	std::ifstream image;
	const char *imagepath="cover.jpg";
	image.open(imagepath);
	if( ! image.is_open() ){
		printf("Can't open %s\n",imagepath);
		return 1;
	}
	image.seekg(0,image.end);
	int imgsize=image.tellg();
	image.seekg(0,image.beg);
	char * imgdata = new char [imgsize];
	image.read(imgdata,imgsize);
	image.close();
	TagLib::ByteVector b(imgdata,imgsize);
	delete[] imgdata;

	TagLib::ID3v2::AttachedPictureFrame *apf=
		new TagLib::ID3v2::AttachedPictureFrame;
	apf->setPicture( b );
	std::cout<< apf->picture().size() <<std::endl;
	apf->setMimeType( "image/jpeg" );
	apf->setDescription( "text" );
	apf->setType(TagLib::ID3v2::AttachedPictureFrame::FrontCover );
	
	
	mpeg->ID3v2Tag(true);
	mpeg->ID3v2Tag()->addFrame( apf );
	
	if( ! mpeg->ID3v2Tag()->isEmpty() )
		printf("ID3v2\n");
	if( ! mpeg->ID3v1Tag()->isEmpty() )
		printf("ID3v1\n");
	std::cout << mpeg->tag()->artist() << std::endl;
	//mpeg->save(TagLib::MPEG::File::ID3v1,true);
	mpeg->save();
}
