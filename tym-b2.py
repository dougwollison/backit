#!/usr/bin/env python
import sys
import base64
import json
import urllib2
import os
import hashlib
from shared import config

account_id = config.get( 'b2', 'account_id' )
account_key = config.get( 'b2', 'account_key' )
bucket = config.get( 'b2', 'bucket' )

class B2 :
	def __init__( self, id, key, bucket = None ) :
		self.account_id = id

		self.authorize( id, key )

		if bucket :
			self.select_bucket( bucket )

	def request( self, url, data, headers ) :
		request = urllib2.Request( url.encode( 'utf-8' ), data, headers )

		response = urllib2.urlopen( request )
		result = json.loads( response.read() )
		response.close()

		return result

	def select_bucket( self, name ) :
		buckets = self.request(
			'%s/b2api/v1/b2_list_buckets' % self.url,
			json.dumps( {
				'accountId': self.account_id
			} ),
			{
				'Authorization': self.token
			}
		)[ 'buckets' ]

		for bucket in buckets :
			if bucket[ 'bucketName' ] == name :
				self.bucket = bucket[ 'bucketId' ]
				break

		return self.bucket

	def authorize( self, id, key ) :
		data = self.request(
			'https://api.backblazeb2.com/b2api/v1/b2_authorize_account',
			None,
			headers = {
				'Authorization': 'Basic ' + base64.b64encode( id + ':' + key ),
			}
		)

		self.token = data[ 'authorizationToken' ]
		self.url = data[ 'apiUrl' ]
		self.part_size = data[ 'recommendedPartSize' ]

	def start_large_file( self, file ) :
		result = self.request(
			'%s/b2api/v1/b2_start_large_file' % self.url,
			json.dumps( {
				'fileName': os.path.basename( file ),
				'contentType': 'b2/x-auto',
				'bucketId': self.bucket,
			} ),
			{
				'Authorization': self.token
			}
		)

		return result[ 'fileId' ]

	def finish_large_file( self, file_id, hash_array ) :
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

	def get_upload_url( self ) :
		result = self.request(
			'%s/b2api/v1/b2_get_upload_url' % self.url,
			json.dumps( {
				'bucketId': self.bucket,
			} ),
			{
				'Authorization': self.token
			}
		)

		return result

	def get_upload_part_url( self, file_id ) :
		result = self.request(
			'%s/b2api/v1/b2_get_upload_part_url' % self.url,
			json.dumps( {
				'fileId': file_id,
			} ),
			{
				'Authorization': self.token
			}
		)

		return result

	def upload_file( self, file ) :
		job = self.get_upload_url()

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
				'X-BZ-File-Name': os.path.basename( file ),
			}
		)

	def upload_large_file( self, file ) :
		file_id = self.start_large_file( file )
		job = self.get_upload_part_url( file_id )

		file_size = os.stat( file ).st_size

		bytes_sent = 0
		part_number = 1
		part_size = self.part_size

		hash_array = []

		fh = open( file, 'rb' )

		while ( bytes_sent < file_size ) :
			if ( file_size - bytes_sent < self.part_size ) :
				part_size = file_size - bytes_sent

			fh.seek( bytes_sent )
			part_data = fh.read( part_size )

			part_hash = hashlib.sha1( part_data ).hexdigest()

			print part_number, part_size

			self.request(
				job[ 'uploadUrl' ],
				part_data,
				{
					'Authorization': job[ 'authorizationToken' ],
					'Content-Length': part_size,
					'X-Bz-Content-Sha1': part_hash,
					'X-BZ-Part-Number': part_number,
				}
			)

			hash_array.append( part_hash )

			bytes_sent += part_size
			part_number += 1

		self.finish_large_file( file_id, hash_array )

	def upload( self, file ) :
		file = os.path.realpath( file )
		file_size = os.stat( file ).st_size

		if file_size > self.part_size :
			self.upload_large_file( file )
		else :
			self.upload_file( file )


api = B2( account_id, account_key, bucket )
