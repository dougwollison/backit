import sys
from configparser import ConfigParser
import os

config = ConfigParser()

project = 'default'
if len( sys.argv ) > 1 :
	project = sys.argv[1]

option = None
if len( sys.argv ) > 2 :
	option = sys.argv[2]

backit_dir = os.path.realpath( os.path.join( __file__, '../../' ) )
conf_dir = os.path.join( backit_dir, 'conf' )

# Read the default config if found
conf_main = os.path.join( conf_dir, 'default.conf' )
if os.path.isfile( conf_main ) :
	config.read( conf_main )

# Read the project config if found
conf_project = os.path.join( conf_dir, project + '.conf' )
if os.path.isfile( conf_project ) :
	config.read( conf_project )

# Alias to ConfigParser.get()
def get( section, name, default=None ) :
	return config.get( section, name, fallback=default )
