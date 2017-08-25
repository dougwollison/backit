#!/usr/bin/env python
import time
import os
import subprocess
from glob import glob
from shared import config

filter = config.get( 'rsync', 'filter' )
log_file = config.get( 'rsync', 'log_file' )
connection = config.get( 'rsync', 'connection' )
source_base = os.path.realpath( config.get( 'rsync', 'source_base' ) )
target_base = os.path.realpath( config.get( 'rsync', 'target_base' ) )

timestamp = time.strftime( '%Y.%m.%d_%H.%M.%S' )
backup_directory = target_base + '/' + timestamp
linkref_directory = target_base + '/latest'

command = [
	'rsync',
	'-vvhrtplHP',
	'-e', 'ssh',
	'--rsync-path', 'sudo rsync',
	'--filter', '. ' + filter,
	'--log-file', log_file,
]

if os.path.exists( linkref_directory ) :
	command = command + [
		'--delete',
		'--delete-excluded',
		'--link-dest', linkref_directory
	]

command = command + [
	connection + ':' + source_base,
	backup_directory
]

os.makedirs( backup_directory )
subprocess.call( command )

os.symlink( backup_directory, linkref_directory )
