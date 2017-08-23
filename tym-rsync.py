#!/usr/bin/env python
import time
import os
import subprocess
from shared import config

filter = config.get( 'rsync', 'filter' )
connection = config.get( 'rsync', 'connection' )
source_base = os.path.realpath( config.get( 'rsync', 'source_base' ) )
target_base = os.path.realpath( config.get( 'rsync', 'target_base' ) )

timestamp = time.strftime( '%Y.%m.%d_%H.%M.%S' )
backup_directory = target_base + '/' + timestamp

os.makedirs( backup_directory )

subprocess.call( [
	'rsync',
	'-vvhrtplHP',
	'-e', 'ssh',
	'--rsync-path', 'sudo rsync',
	'--filter', '. ' + filter,
	connection + ':' + source_base,
	backup_directory
] )
