import ConfigParser
import os
from subprocess import call
config = ConfigParser.ConfigParser()
config.read( os.path.dirname( os.path.realpath( __file__ ) ) + '/tym.conf' )
