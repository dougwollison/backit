#!/usr/bin/env python3
import sys
import os
import shutil
import hashlib
from glob import glob
from shared import config, project

count = 1
if len( sys.argv ) > 2 :
	count = int( sys.argv[2] )

for x in range( count ) :
	backup_dir = os.path.realpath( config.get( 'rsync', 'target_base' ) )

	# Get the earliest backup
	archive_dir = sorted( glob( backup_dir + '/*' ) )[0]

	# Check if it's flagged as being worked on
	hash = hashlib.md5( archive_dir ).hexdigest()
	working_file = '/tmp/backit-%s-%s.working' % ( project, hash )

	if os.path.isfile( working_file ) :
		print( 'Unable to delete ' + archive_dir + ' (archive in progress)' )
		sys.exit( 0 )

	print( 'Deleting ' + archive_dir + '...' )
	shutil.rmtree( archive_dir )
	print( 'Done.' )
