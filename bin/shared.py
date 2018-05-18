import sys
from configparser import ConfigParser
import os

config = ConfigParser()

project = 'default'
if len( sys.argv ) > 1 :
	project = sys.argv[1]

dir = os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) ) + '/conf'

conf_main = dir + '/default.conf'
conf_project = dir + '/' + project + '.conf';

config.read( conf_main )
if os.path.isfile( conf_project ) :
	config.read( conf_project )
