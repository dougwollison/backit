#!/usr/bin/env python3
import sys
import os
import shutil
import hashlib
from glob import glob
from shared import config, project

keep = int( config.get( 'storage', 'keep' ) )
if len( sys.argv ) > 2 :
	keep = int( sys.argv[2] )

backup_dir = os.path.realpath( config.get( 'rsync', 'target_base' ) )

archives = sorted( glob( backup_dir + '/20*_*' ) )
count = len( archives )

print( 'Found %d archive(s).' % count );

if count > keep :
	print( 'Need to delete earliest %d.' % ( count - keep ) )

	n = 0
	while count > keep :
		# Get the earliest backup
		archive_dir = archives[ n ]

		# Check if it's flagged as being worked on
		hash = hashlib.md5( archive_dir.encode( 'utf-8' ) ).hexdigest()
		working_file = '/tmp/backit-%s-%s.working' % ( project, hash )

		if os.path.isfile( working_file ) :
			print( 'Unable to delete ' + archive_dir + ' (archive in progress)' )
			sys.exit( 0 )

		print( 'Deleting ' + archive_dir + '...' )
		shutil.rmtree( archive_dir )
		print( 'Done.' )

		count -= 1
		n += 1
else:
	print( 'No cleanup necessary.' )
