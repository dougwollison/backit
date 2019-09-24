import sys
import os
import configparser

project = 'default'
if len( sys.argv ) > 1 :
	project = sys.argv[1]

option = None
if len( sys.argv ) > 2 :
	option = sys.argv[2]

config = configparser.ConfigParser()

# Alias to ConfigParser.get()
def get( section, name, default=None ) :
	return config.get( section, name, fallback=default )

# Build a directory path
def pathit( start, *parts ) :
	path = [ start ]
	for part in parts :
		path.append( part.strip( '/' ) )

	path = list( filter( None, path ) )

	return '/'.join( path )

backit_dir = os.path.realpath( pathit( __file__, '../../' ) )
conf_dir = pathit( backit_dir, 'conf' )

# Read the default config if found
conf_main = pathit( conf_dir, 'default.conf' )
if os.path.isfile( conf_main ) :
	config.read( conf_main )

# Read the project config if found
conf_project = pathit( conf_dir, project + '.conf' )
if os.path.isfile( conf_project ) :
	config.read( conf_project )
