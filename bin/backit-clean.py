#!/usr/bin/env python
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
	working_file = '/tmp/backit-%s-%s.working' % ( project, hash );

	# If not being worked on, delete
	if not os.path.isfile( working_file ) :
		print 'Deleting ' + archive_dir + '...'

		shutil.rmtree( archive_dir )

		print 'Done.'
