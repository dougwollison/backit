"""A bare-bones wrapper for the B2 api"""

import os
import base64
import json
import urllib2
import hashlib

class B2 :
	def __init__( self, id, key ) :
		"""Authorize the account"""

		self.account_id = id
		self.authorize( id, key )

		self.get_buckets()

	def request( self, url, data, headers ) :
		"""Perform the actual API request and return the result"""

		# Create and send the request
		request = urllib2.Request( url.encode( 'utf-8' ), data, headers )
		response = urllib2.urlopen( request )

		# Parse the result
		result = json.loads( response.read() )
		response.close()

		return result

	def authorize( self, id, key ) :
		"""Authorize the account, store the token, url, and part size"""

		data = self.request(
			'https://api.backblazeb2.com/b2api/v1/b2_authorize_account',
			None,
			headers = {
				'Authorization': 'Basic ' + base64.b64encode( id + ':' + key ),
			}
		)

		# Store the credentials and settings
		self.token = data[ 'authorizationToken' ]
		self.url = data[ 'apiUrl' ]
		self.part_size = data[ 'recommendedPartSize' ]

	def get_buckets( self ) :
		"""Get and compile the Name > ID list of buckets on the account"""

		result = self.request(
			'%s/b2api/v1/b2_list_buckets' % self.url,
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

		cache = '/tmp/b2-fileid-' + hashlib.sha1( savename ).hexdigest()

		# Check if file was started
		if os.path.isfile( cache ) :
			# Pull from cache
			input = open( cache );
			result = json.load( input )
			input.close()
		else :
			# Request a fresh job
			result = self.request(
				'%s/b2api/v1/b2_start_large_file' % self.url,
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
			with open( cache, 'w' ) as output:
				json.dump( result, output )

		return result[ 'fileId' ]

	def finish_large_file( self, file_id, hash_array ) :
		"""Notify that the large file upload has finished"""

		result = self.request(
			'%s/b2api/v1/b2_finish_large_file' % self.url,
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

		result = self.request(
			'%s/b2api/v1/b2_get_upload_url' % self.url,
			json.dumps( {
				'bucketId': bucket,
			} ),
			{
				'Authorization': self.token
			}
		)

		return result

	def get_upload_part_url( self, file_id ) :
		"""Get the URL to use for uploading a file part to the bucket"""

		cache = '/tmp/b2-job-' + file_id

		# Check if the upload was started
		if os.path.isfile( cache ) :
			# Pull from cache
			input = open( cache );
			result = json.load( input )
			input.close()
		else :
			# Request a fresh upload
			result = self.request(
				'%s/b2api/v1/b2_get_upload_part_url' % self.url,
				json.dumps( {
					'fileId': file_id,
				} ),
				{
					'Authorization': self.token
				}
			)

			# Default values for progress tracking
			result['bytes_sent'] = 0
			result['part_number'] = 1
			result['hash_array'] = []

			# Save to cache
			with open( cache, 'w' ) as output:
				json.dump( result, output )

		return result

	def upload_file( self, file, bucket, savename ) :
		"""Perform a standard file upload"""

		job = self.get_upload_url( bucket )

		fh = open( file )
		data = fh.read()

		hash = hashlib.sha1( data ).hexdigest()

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

	def upload_large_file( self, file, bucket, savename ) :
		"""Perform a large file upload"""

		# Start the file and upload job
		file_id = self.start_large_file( file, bucket, savename )
		job = self.get_upload_part_url( file_id )

		cache = '/tmp/b2-job-' + file_id

		file_size = os.stat( file ).st_size
		part_size = self.part_size

		fh = open( file, 'rb' )

		while ( job['bytes_sent'] < file_size ) :
			if ( file_size - job['bytes_sent'] < self.part_size ) :
				part_size = file_size - job['bytes_sent']

			fh.seek( job['bytes_sent'] )
			part_data = fh.read( part_size )
			part_hash = hashlib.sha1( part_data ).hexdigest()

			print job['part_number'], part_size

			self.request(
				job[ 'uploadUrl' ],
				part_data,
				{
					'Authorization': job[ 'authorizationToken' ],
					'Content-Length': part_size,
					'X-Bz-Content-Sha1': part_hash,
					'X-BZ-Part-Number': job['part_number'],
				}
			)

			# Update the progress
			job['hash_array'].append( part_hash )
			job['bytes_sent'] += part_size
			job['part_number'] += 1

			# Save to cache
			with open( cache, 'w' ) as output:
				json.dump( job, output )

		self.finish_large_file( file_id, job['hash_array'], savename )

		# Delete cache files
		os.remove( '/tmp/b2-fileid-' + hashlib.sha1( savename ).hexdigest() )
		os.remove( '/tmp/b2-job-' + file_id )

	def upload( self, file, bucket, savename ) :
		"""Determine the bucket ID, savename, and what upload method to use"""

		file = os.path.realpath( file )
		file_size = os.stat( file ).st_size

		bucket = bucket.split( '/', 1 );
		bucket_name = bucket[0]
		bucket_path = ''
		if len( bucket ) > 1 :
			bucket_path = bucket[1]

		bucket_id = self.buckets[ bucket_name ]

		if not savename :
			savename = os.path.basename( file )
		else :
			savename = ( bucket_path + '/' + savename ).replace( '//', '/' ).strip( '/' )

		if file_size > self.part_size :
			self.upload_large_file( file, bucket_id, savename )
		else :
			self.upload_file( file, bucket_id, savename )
