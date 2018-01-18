#!/usr/bin/env python
import os
import tarfile
import shutil
import hashlib
from glob import glob
from api import B2
from shared import config

backup_dir = os.path.realpath( config.get( 'rsync', 'target_base' ) )
tarballs_dir = os.path.realpath( config.get( 'backblaze', 'tarballs_dir' ) )
part_size = int( config.get( 'backblaze', 'part_size' ) )
account_id = config.get( 'backblaze', 'account_id' )
account_key = config.get( 'backblaze', 'account_key' )
bucket = config.get( 'backblaze', 'bucket' )

folders = config.get( 'backblaze', 'separate_folders' )

api = B2( account_id, account_key, part_size )

def mkdir( dir ) :
	"""Shorthand for creating a directory that doesn't exist yet"""

	if not os.path.exists( dir ) :
		os.makedirs( dir )

	return dir

mkdir( tarballs_dir )

def make_archive( folder, parent = '' ) :
	"""Create a gzipped tarball of the folder and upload it to B2"""

	basename = os.path.basename( folder );
	b2_filename = os.path.basename( parent ) + '/' + basename + '.tgz'
	tar_file = tarballs_dir + '/' + b2_filename
	tar_dir = os.path.dirname( tar_file )

	# These files will flag the status of the file
	hash = hashlib.md5( tar_file ).hexdigest()
	ready_file = '/tmp/backit-ready-' + hash
	done_file = '/tmp/backit-done-' + hash

	# If straight up done, skip
	if os.path.isfile( done_file ) :
		print 'Skipping ' + folder
		return

	mkdir( tar_dir )

	# Create the archive if not yet ready
	if not os.path.isfile( ready_file ) :
		print 'Archiving ' + folder + '...'

		tar = tarfile.open( tar_file, 'w:gz' )
		tar.add( folder, arcname = basename )
		tar.close()

		# Flag as ready
		open( ready_file, 'a' ).close()

		print 'Done.'

	print 'Uploading ' + tar_file + '...'

	# Upload to B2
	api.upload( tar_file, bucket, b2_filename )

	print 'Done.'

	print 'Cleaning up...'

	# Remove the tar file and ready flag
	os.remove( tar_file )
	os.remove( ready_file )

	# Flag as done
	open( done_file, 'a' ).close()

	print 'Done.'

archive_dir = sorted( glob( backup_dir + '/*' ) )[0]

if folders :
	folders = folders.split( ':' )

	for folder in folders :
		folder = archive_dir + folder

		for dir in sorted( glob( folder ) ) :
			make_archive( dir, archive_dir )

else :
	make_archive( archive_dir )

shutil.rmtree( tarballs_dir )
