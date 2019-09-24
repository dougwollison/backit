import os
import json

class JobFile :
	def __init__( self, folder, initStatus = None ) :
		"""Load the status file, or create if defaults are provided"""

		self.file = folder + '.json'
		self.data = {
			'status': initStatus,
			'files': {}
		}

		if self.exists() :
			input = open( self.file )
			self.data = json.load( input )
			input.close()

		elif initStatus != None :
			self.save()

	def exists( self ) :
		return os.path.isfile( self.file )

	def save( self ) :
		with open( self.file, 'w' ) as output :
			json.dump( self.data, output )
			output.close()

	def isStatus( self, status ) :
		return self.data['status'] == status

	def setStatus( self, status ) :
		self.data['status'] == status
		self.save()

	def isFile( filename, status ) :
		return self.data['files'][ filename ] == status

	def logFile( filename, status ) :
		self.data['files'][ filename ] == status
		self.save()
