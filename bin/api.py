"""A bare-bones wrapper for the B2 api"""

import os
import sys
import gc
import math
import time
import string
import base64
import json
import hashlib
import urllib.request as urlreq
import urllib.error as urlerr

def is_reset_error( e ) :
	return isinstance( e.reason, IOError ) and ( e.reason.errno == 104 or e.reason.errno == 111 )

class B2 :
	def __init__( self, id, key, part_size ) :
		"""Initialize and authorize"""

		self.account_id = id
		self.account_key = key
		self.part_size = part_size

		# Create/open log file
		self.progress_log = open( '/var/log/backit/' + time.strftime( '%Y.%m.%d_%H.%M.%S' ), 'a' )

		# Authorize and fetch bucket list
		self.log( 'Authorizing...' )
		self.authorize()
		self.get_buckets()

	def log( self, *message_parts ) :
		"""Log the message for the debug"""

		timestamp = '[' + time.strftime( '%H:%M:%S' ) + ']'
		message = " ".join( str( m ) for m in message_parts )

		self.progress_log.write( timestamp + " " + message + "\n" )
		print( message )

	def pause( self, message, action = 'Retrying', seconds = 10 ) :
		"""Log a pause in the progress and wait"""

		self.log( '%s. %s in %d seconds...' % ( message, action, seconds ) )
		time.sleep( seconds )

	def fail( self, message ) :
		"""Log the final message and abort the script"""

		self.log( '%s. Aborting...' % message )

		self.progress_log.close()
		sys.exit()

	def request( self, url, data, headers ) :
		"""Perform the actual API request and return the result"""

		self.log( '--', url )

		if data and not isinstance( data, bytes ) :
			data = data.encode( 'utf-8' )

		# Create and send the request
		request = urlreq.Request( url, data, headers )
		response = urlreq.urlopen( request )

		# Parse the result
		result = json.loads( str( response.read(), 'utf-8' ) )
		response.close()

		return result

	def try_request( self, url, data, headers ) :
		"""Attempt the request, reauthorizing or retrying if needed"""

		try :
			return self.request( url, data, headers );

		except urlerr.HTTPError as e :
			if e.code == 429 :
				self.fail( '--- Request limit imposed' )

			if e.code >= 500 :
				self.log( '--- Server error' )

				return self.try_request( url, data, headers );

			if e.code == 401 :
				self.log( '--- Auth error', 'Reauthorizing', 5 )
				self.authorize()

				return self.try_request( url, data, headers );

			else :
				raise

		except urlerr.URLError as e :
			if is_reset_error( e ) :
				self.pause( '--- Connection error' )

				return self.try_request( url, data, headers );

			else :
				self.fail( 'Error connecting to B2: ' + str( e ) )

	def authorize( self ) :
		"""Authorize the account, store the token, url, and part size"""

		# Fetch the connection info needed
		try :
			auth = self.account_id + ':' + self.account_key
			data = self.request(
				'https://api.backblazeb2.com/b2api/v2/b2_authorize_account',
				None,
				headers = {
					'Authorization': 'Basic ' + str( base64.b64encode( str.encode( auth ) ), 'utf-8' ),
				}
			)

		except urlerr.HTTPError as e :
			self.fail( 'Error authorizing account: ' + str( e ) )

		except urlerr.URLError as e :
			if is_reset_error( e ) :
				self.pause( '--- Connection reset/refused: ' + str( e ), 'Retrying', 5 )

				self.authorize()

			else :
				self.fail( 'Error connecting to B2: ' + str( e ) )

		# Store the credentials and settings
		self.token = data[ 'authorizationToken' ]
		self.url = data[ 'apiUrl' ]

		# If a custom part size is not specified, use the one from the API
		if self.part_size == 0 :
			self.part_size = data[ 'recommendedPartSize' ]

	def get_buckets( self ) :
		"""Get and compile the Name > ID list of buckets on the account"""

		# Fetch the bucket list
		result = self.try_request(
			'%s/b2api/v2/b2_list_buckets' % self.url,
			json.dumps( {
				'accountId': self.account_id
			} ),
			{
				'Authorization': self.token
			}
		)[ 'buckets' ]

		# Store the listing of bucket IDs
		self.buckets = {}
		for entry in result :
			self.buckets[ entry[ 'bucketName' ] ] = entry[ 'bucketId' ]

	def start_large_file( self, file, bucket, savename ) :
		"""Submit a request for a large file upload, return the file ID to use"""

		# Generate a cache filename to use
		cache = '/tmp/b2-fileid-' + hashlib.sha1( savename.encode( 'utf-8' ) ).hexdigest()

		# Check if file was started
		if os.path.isfile( cache ) :
			# Pull from cache
			input = open( cache );
			result = json.load( input )
			input.close()

		else :
			# Request a fresh job
			result = self.try_request(
				'%s/b2api/v2/b2_start_large_file' % self.url,
				json.dumps( {
					'fileName': savename,
					'contentType': 'b2/x-auto',
					'bucketId': bucket,
				} ),
				{
					'Authorization': self.token
				}
			)

			# Save to cache
			with open( cache, 'w' ) as output :
				json.dump( result, output )
				output.close()

		return result[ 'fileId' ]

	def finish_large_file( self, file_id, hash_array ) :
		"""Notify that the large file upload has finished"""

		# Submit the hash array to confirm the file is finished
		result = self.request(
			'%s/b2api/v2/b2_finish_large_file' % self.url,
			json.dumps( {
				'fileId': file_id,
				'partSha1Array': hash_array,
			} ),
			{
				'Authorization': self.token
			}
		)

	def get_upload_url( self, bucket ) :
		"""Get the URL to use for uploading a file to the bucket"""

		# Get the needed information for the upload job
		result = self.try_request(
			'%s/b2api/v2/b2_get_upload_url' % self.url,
			json.dumps( {
				'bucketId': bucket,
			} ),
			{
				'Authorization': self.token
			}
		)

		return result

	def try_upload_file( self, job, data, savename, hash ) :
		"""Perform the actual file upload"""

		try :
			# Send the file with the hash and desired savename
			self.request(
				job[ 'uploadUrl' ],
				data,
				{
					'Authorization': job[ 'authorizationToken' ],
					'Content-Type': 'bz/x-auto',
					'X-Bz-Content-Sha1': hash,
					'X-BZ-File-Name': savename,
				}
			)

		except urlerr.HTTPError as e :
			if e.code == 429 :
				self.fail( '--- Request limit imposed' )

			if e.code >= 400 :
				self.pause( '--- Server/Client error', 'Renewing url/token', 10 )

				# Try fetching a new url/token in case they expired
				renewed = self.get_upload_url( job['bucket_id'] )
				self.try_upload_file( renewed, data, savename, hash )

			else :
				raise

		except urlerr.URLError as e :
			if is_reset_error( e ) :
				self.pause( '--- Connection reset/refused: ' + str( e ), 'Retrying', 5 )

				self.try_upload_file( job, data, savename, hash )

			if isinstance( e.reason, IOError ) and e.reason.errno == 32 :
				self.pause( '--- Broken pipe', 'Renewing url/token', 10 )

				# Try fetching a new url/token in case they expired
				renewed = self.get_upload_url( job['bucket_id'] )
				self.try_upload_file( renewed, data, savename, hash )

			else :
				self.fail( 'Error connecting to B2: ' + str( e ) )

	def upload_file( self, file, bucket, savename ) :
		"""Perform a standard file upload"""

		# Get the job data; url to upload to and token to authorize with
		job = self.get_upload_url( bucket )

		# Store the file ID for reference
		job['bucket_id'] = bucket

		# Load the file, compile the hash
		fh = open( file, 'rb' )
		data = fh.read()
		hash = hashlib.sha1( data ).hexdigest()

		self.try_upload_file( job, data, savename, hash )

	def get_upload_part_url( self, file_id, renew=False ) :
		"""Get the URL to use for uploading a file part to the bucket"""

		# Generate a cache filename to use
		cache = '/tmp/b2-job-' + file_id

		# Default job data
		upload = {
			'bytes_sent': 0,
			'part_number': 0,
			'hash_array': [],
		}

		# Check if the upload was started
		if os.path.isfile( cache ) :
			# Pull from cache
			input = open( cache, 'r' )
			upload = json.load( input )
			input.close()

		if not ( 'fileId' in upload ) or renew :
			# Get the needed information for the part upload
			result = self.try_request(
				'%s/b2api/v2/b2_get_upload_part_url' % self.url,
				json.dumps( {
					'fileId': file_id,
				} ),
				{
					'Authorization': self.token
				}
			)

			# merge into job
			upload = { **upload, **result }

		# Save to cache
		with open( cache, 'w' ) as output :
			json.dump( upload, output )
			output.close()

		return upload

	def try_upload_file_part( self, job, data, size, hash ) :
		"""Perform the actual file part upload"""

		try :
			self.request(
				job[ 'uploadUrl' ],
				data,
				{
					'Authorization': job[ 'authorizationToken' ],
					'Content-Length': size,
					'X-Bz-Content-Sha1': hash,
					'X-BZ-Part-Number': job['part_number'],
				}
			)

		except urlerr.HTTPError as e :
			if e.code == 429 :
				self.fail( '--- Request limit imposed' )

			if e.code >= 400 :
				self.pause( '--- Server/Client error', 'Renewing url/token', 10 )

				# Try fetching a new url/token in case they expired
				renewed = self.get_upload_part_url( job['fileId'], 'renew' )
				self.try_upload_file_part( renewed, data, size, hash )

			else :
				raise

		except urlerr.URLError as e :
			if is_reset_error( e ) :
				self.pause( '--- Connection reset/refused: ' + str( e ), 'Retrying', 5 )

				self.try_upload_file_part( job, data, size, hash )

			if isinstance( e.reason, IOError ) and e.reason.errno == 32 :
				self.pause( '--- Broken pipe', 'Renewing url/token', 10 )

				# Try fetching a new url/token in case they expired
				renewed = self.get_upload_part_url( job['fileId'], 'renew' )
				self.try_upload_file_part( renewed, data, size, hash )

			else :
				self.fail( 'Error connecting to B2: ' + str( e ) )

	def upload_large_file( self, file, bucket, savename ) :
		"""Perform a large file upload"""

		# Start the file and upload job
		file_id = self.start_large_file( file, bucket, savename )
		job = self.get_upload_part_url( file_id )

		# Generate a cache filename to use
		cache = '/tmp/b2-job-' + file_id

		# Get the total file size and part size to use
		file_size = os.stat( file ).st_size
		part_size = self.part_size
		part_total = math.ceil( file_size / part_size )

		# Open the file, begin reading chunks
		fh = open( file, 'rb' )
		while ( job['bytes_sent'] < file_size ) :
			# If finishing the file, size is the remaining about
			if ( file_size - job['bytes_sent'] < self.part_size ) :
				part_size = file_size - job['bytes_sent']

			# Get the part chunk and hash of it
			fh.seek( job['bytes_sent'] )
			part_data = fh.read( part_size )
			part_hash = hashlib.sha1( part_data ).hexdigest()

			# Attempt to upload the part
			self.log( '- Uploading Part', job['part_number'], 'of', part_total, part_size )
			self.try_upload_file_part( job, part_data, part_size, part_hash )

			# Paranoid cleanup
			del part_data
			gc.collect()

			# Update the progress
			job['hash_array'].append( part_hash )
			job['bytes_sent'] += part_size
			job['part_number'] += 1

			# Save to cache
			with open( cache, 'w' ) as output :
				json.dump( job, output )
				output.close()

		# Close the file and finalize the upload
		fh.close()
		self.finish_large_file( file_id, job['hash_array'] )

		# Delete cache files
		os.remove( '/tmp/b2-fileid-' + hashlib.sha1( savename.encode( 'utf-8' ) ).hexdigest() )
		os.remove( '/tmp/b2-job-' + file_id )

	def upload( self, file, bucket, savename ) :
		"""Determine the bucket ID, savename, and what upload method to use"""

		# Get the file size
		file = os.path.realpath( file )
		file_size = os.stat( file ).st_size

		# Determine the bucket ID
		bucket = bucket.split( '/', 1 );
		bucket_name = bucket[0]
		bucket_path = ''
		if len( bucket ) > 1 :
			bucket_path = bucket[1]

		bucket_id = self.buckets[ bucket_name ]

		# Compile the savename
		if not savename :
			savename = os.path.basename( file )
		else :
			savename = ( bucket_path + '/' + savename ).replace( '//', '/' ).strip( '/' )

		# Upload based on appropriate method
		if file_size > self.part_size :
			self.upload_large_file( file, bucket_id, savename )
		else :
			self.upload_file( file, bucket_id, savename )
