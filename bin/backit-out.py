#!/usr/bin/env python
import os
import tarfile
import shutil
from glob import glob
from api import B2
from shared import config

backup_dir = os.path.realpath( config.get( 'rsync', 'target_base' ) )
tarballs_dir = os.path.realpath( config.get( 'backblaze', 'tarballs_dir' ) )
account_id = config.get( 'backblaze', 'account_id' )
account_key = config.get( 'backblaze', 'account_key' )
bucket = config.get( 'backblaze', 'bucket' )

folders = config.get( 'backblaze', 'separate_folders' )

api = B2( account_id, account_key )

def mkdir( dir ) :
	"""Shorthand for creating a directory that doesn't exist yet"""

	if not os.path.exists( dir ) :
		os.makedirs( dir )

	return dir

mkdir( tarballs_dir )

def make_archive( folder, parent = '' ) :
	"""Create a gzipped tarball of the folder and upload it to B2"""

	print 'Archiving ' + folder + '...'

	basename = os.path.basename( folder );
	b2_filename = os.path.basename( parent ) + '/' + basename + '.tgz'
	tar_file = tarballs_dir + '/' + b2_filename
	tar_dir = os.path.dirname( tar_file )

	mkdir( tar_dir )

	tar = tarfile.open( tar_file, 'w:gz' )
	tar.add( folder, arcname = basename )
	tar.close()

	print 'Done. Uploading ' + tar_file + '...'

	api.upload( tar_file, bucket, b2_filename )

	print 'Done. cleaning up...'

	os.remove( tar_file )
	os.rmdir( tar_dir )

	print 'Done.'

archive_dir = sorted( glob( backup_dir + '/*' ) )[0]

if folders :
	folders = folders.split( ':' )

	for folder in folders :
		folder = archive_dir + folder

		for dir in glob( folder ) :
			make_archive( dir, archive_dir )

else :
	make_archive( archive_dir )

shutil.rmtree( tarballs_dir )
