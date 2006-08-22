#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Mahangu Weerasinghe (mahangu@gmail.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import httplib, urllib, os, ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('conf/main.conf'))
server = config.get("main","server")
path = config.get ("main", "path")
port = config.get("main","port")
message = config.get ("main", "message")
email = config.get ("main", "email")

url = 'http://%s%s'%(server,path)

final = "" #gotta find a better way to do this

def send_post(logs, message = message, email = email, server = server, path= path, port = port):

	print logs #error catching, for now

	params = urllib.urlencode({'message': message, 'email': email, 'logs': logs})
	headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
	conn = httplib.HTTPConnection('%s:%s'%(server, port))
	conn.request("POST", path, params, headers)
	response = conn.getresponse()	
	return response.status # response.reason
	data = response.read()
	conn.close()

def get_path(path):
	location = open(path)
	log = location.read()
	log = '<br /><em>%s</em><br />%s' % (path,log)
	return log

def get_dump(dump):
	location = os.popen(dump)
	log = location.read()
	log = '<br /><em>%s</em><br />%s' % (dump,log)
	return log

def add_final(text):
	global final
	finale = final
	final = '%s\n\n%s'%(finale,text)
	return final

def get_final():
	global final
	return final

def send_curl (logs, message = message, email = email, server = server, path= path, port = port):

	logs = logs.replace("\"","")
	curlstring = 'curl --form-string "message=%s" --form-string "email=%s" --form-string "logs=%s" %s'%(message,email,logs,url)
	dump = os.popen(curlstring)	
	clog = dump.read()
	return clog


