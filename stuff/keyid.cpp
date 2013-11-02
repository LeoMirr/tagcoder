#include <taglib/fileref.h>
#include <taglib/mpegfile.h>
#include <taglib/id3v1tag.h>
#include <taglib/id3v2tag.h>
#include <taglib/id3v2frame.h>
#include <taglib/tbytevector.h>
#include <taglib/attachedpictureframe.h>
#include <stdio.h>
#include <typeinfo>
#include <iostream>
#include <fstream>

class MyClass : public TagLib::ID3v2::Frame{
	public:
		static TagLib::String frameID2Key( const TagLib::ByteVector &b ){
			return frameIDToKey( b );
		}

};

int main(int argc,char **argv){
	if( argc == 1 ){
		printf("You must specify one at least one argumet\n");
		return 1;
	}
	std::cout << MyClass::frameID2Key( argv[1] ) << std::endl;
}

