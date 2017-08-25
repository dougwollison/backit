#!/usr/bin/env python
import os
import tarfile
from glob import glob
from api import B2
from shared import config

backup_dir = os.path.realpath( config.get( 'rsync', 'target_base' ) )
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

tmp_dir = mkdir( '/tmp/tym2' )

def make_archive( folder, parent = '' ) :
	"""Create a gzipped tarball of the folder and upload it to B2"""

	basename = os.path.basename( folder );
	b2_filename = os.path.basename( parent ) + '/' + basename + '.tgz'
	archive_file = tmp_dir + '/' + b2_filename

	mkdir( os.path.dirname( archive_file ) )

	tar = tarfile.open( archive_file, 'w:gz' )
	tar.add( folder, arcname = basename )
	tar.close()

	api.upload( archive_file, bucket, b2_filename )
	os.remove( archive_file )

archive_dir = sorted( glob( backup_dir + '/*' ) )[0]

if folders :
	folders = folders.split( ':' )

	for folder in folders :
		folder = archive_dir + folder

		for dir in glob( folder ) :
			make_archive( dir, archive_dir )

else :
	make_archive( archive_dir )
