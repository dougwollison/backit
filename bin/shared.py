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

dir = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) ) + '/conf'

conf_main = dir + '/default.conf'
conf_project = dir + '/' + project + '.conf';

if os.path.isfile( conf_main ) :
	config.read( conf_main )

if os.path.isfile( conf_project ) :
	config.read( conf_project )
