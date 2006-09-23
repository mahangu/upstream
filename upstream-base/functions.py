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

main_config = ConfigParser.ConfigParser()
list_config = ConfigParser.ConfigParser()

server = None
path = None
port = None
message = None
email = None

url = 'http://%s%s'%(server,path)

final = "" #gotta find a better way to do this




# Allow imports from different locations than the direct location of the function module
# This should be raised if any functions are called with an unset configuration dir
# that requires access to the configuration files
class ConfDirUnsetException(Exception):
	def __init__(self):
		Exception.__init__(self)
	def __str__(self):
		return "Configuration directory is unset!"
		
class NoSuchItemException(Exception):
	def __init__(self):
		Exception.__init__(self)
	def __str__(self):
		return "No such item exists!"
		
	

conf_dir = None
conf_dir_set = False
def set_conf_dir(path_to_dir):
	global conf_dir
	global conf_dir_set	
	
	conf_dir = path_to_dir
	conf_dir_set = True

	# Main configuration
	main_config.readfp(open(path_to_dir + 'main.conf'))		
	# List configurations
	list_config.readfp(open(path_to_dir + "list.conf"))
	# Actually perform the read
	read_conf()
	
	
def read_conf():
	global server
	global path
	global port
	global message
	global email
	
	server = main_config.get("main","server")
	path = main_config.get ("main", "path")
	port = main_config.get("main","port")
	message = main_config.get ("main", "message")
	email = main_config.get ("main", "email")

	
# which_conf should be either main or list
def get_conf_item(which_conf, section, attr):
	if conf_dir_set:
		if which_conf == "main":
			return main_config.get(section, attr)
		else:
			return list_config.get(section, attr)
	else:
		raise ConfDirUnsetException
		
# Provide a way of getting all sections
def get_conf_sections(which_conf):
	print conf_dir_set
	if conf_dir_set:
		if which_conf == "main":
			return main_config.sections()
		else:
			return list_config.sections()
	else:
		raise ConfDirUnsetException
		

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

def send_curl (logs, message = message, email = email):

	logs = logs.replace("\"","")

	if not conf_dir_set:
		raise ConfDirUnsetException
	# Remove duplicate code, we should use only the global
	#config = ConfigParser()
	#main_config.readfp(open('conf/main.conf'))
	url = main_config.get("post", "url")
	name_field = main_config.get("post", "name_field")
	title_field = main_config.get("post", "title_field")
	msg_field = main_config.get("post", "msg_field")
	misc = main_config.get("post", "misc")
	referer = main_config.get("post", "referer")

	# Prepare Curl object
	import pycurl
	from urllib import urlencode
	from StringIO import StringIO
	c = pycurl.Curl()
	c.setopt(pycurl.URL, url)
	c.setopt(pycurl.POST, 1)
	post_data = { name_field: "Upstream<%s>"%email, title_field: message, msg_field: logs }
	c.setopt(pycurl.POSTFIELDS, urlencode(post_data)+misc)
	c.setopt(pycurl.REFERER, referer)
	clog = StringIO()
	c.setopt(pycurl.WRITEFUNCTION, clog.write)
	c.perform()

	return clog.getvalue()
	
