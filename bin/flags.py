import os
import hashlib
from shared import project

HASHES = {}
def filename( file, action ) :
	"""Create the name for the flag file"""

	# Cache hashes for sanity
	if file not in HASHES :
		hash = hashlib.md5( file.encode( 'utf-8' ) ).hexdigest()
		HASHES[ file ] = hash

	return '/tmp/backit-%s-%s.%s' % ( project, HASHES[ file ], action )

def write( file, action ) :
	"""Create the specified flag file"""

	open( filename( file, action ), 'a' ).close()

def check( file, action ) :
	"""Check if the specified flag file exists"""

	return os.path.exists( filename( file, action ) )

def remove( file, action ) :
	"""Remove the specified flag file"""

	if check( file, action ) :
		os.remove( filename( file, action ) )
