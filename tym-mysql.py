#!/usr/bin/env python
import time
import os
import re
import subprocess
import pymysql
import gzip
from shared import config

pattern = re.compile( '(information_schema|performance_schema|apsc|atmail|horde|mysql|psa|roundcubemail|sitebuilder5|phpmyadmin_\w+)' );

hostname = config.get( 'mysql', 'hostname' )
username = config.get( 'mysql', 'username' )
password = config.get( 'mysql', 'password' )
destination = os.path.realpath( config.get( 'mysql', 'destination' ) )

timestamp = time.strftime( '%Y.%m.%d_%H.%M.%S' )
dump_prefix = destination + '/' + timestamp

connection = pymysql.connect( hostname, username, password )

with connection.cursor() as cursor:
	cursor.execute( 'SHOW DATABASES' )
	databases = cursor.fetchall()

for database in databases :
	if not pattern.match( database[0] ) :
		dump = subprocess.check_output( [
			'mysqldump',
			'--force',
			'--opt',
			'--user', username,
			'-p%s' % password,
			'-B', database[0]
		] )

		file = '%s-%s.sql.gz' % ( dump_prefix, database[0] )

		with gzip.open( file, 'wb' ) as output :
			output.write( dump )
