import ConfigParser
import os
config = ConfigParser.ConfigParser()
config.read( os.path.dirname( os.path.realpath( __file__ ) ) + '/tym.conf' )
