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



