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

import httplib, urllib, os, ConfigParser, glob, sys

main_config = ConfigParser.ConfigParser()
list_config = ConfigParser.ConfigParser()

#server = None
#path = None
#port = None

email = None
module = None
module_path = None
message = None

final = None




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

modules_dir = None
modules_dir_set = False

def set_modules_dir(path_to_dir):
	global modules_dir
	global modules_dir_set
	
	modules_dir = path_to_dir
	modules_dir_set = True

def read_module(which_module = None):
	default_module = get_conf_item("main", "main", "default_module")
	
	if modules_dir_set:
		if os.path.isfile("%s/%s.py"%(modules_dir,which_module)):
			print which_module
			global module
			global module_path
			
			module = which_module
			module_path = "%s%s.py"%(modules_dir,which_module)
			
			print module_path
			
			print "Looking good partner, your support request is on its way."
			
			return True
					
		else:
			if os.path.isfile("%s/%s.py"%(modules_dir,default_module)):
		
				print "No module specified, using the default module."
				
				module_path = "%s%s.py"%(modules_dir,default_module)
			
				print module_path
				
					
				return True
		
			else :	
			
			
				print "No ouput module was found. Cannot continue."
				sys.exit(1)
				
				return False
	else:
		print "Your Modules directory is not set. I don't know where to look for modules."

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
	# read_conf()
	
	
#def read_conf():
# Depecrated as of September 26th 2006. These variables are now loaded by individual /modules/.py modules.
	#global server
	#global path
	#global port
	#global message
	#global email
	
	#server = main_config.get("main","server")
	#path = main_config.get ("main", "path")
	#port = main_config.get("main","port")
	#message = main_config.get ("main", "message")
	#email = main_config.get ("main", "email")

	
# which_conf should be either main or list
def get_conf_item(which_conf, section, attr):
	if conf_dir_set:
		if which_conf == "main":
			return main_config.get(section, attr)
		elif which_conf == "list":
			return list_config.get(section, attr)
		else:
			raise NoSuchItemException
	else:
		raise ConfDirUnsetException
		
# Provide a way of getting all sections
def get_conf_sections(which_conf):
	print conf_dir_set
	if conf_dir_set:
		if which_conf == "main":
			return main_config.sections()
		elif which_conf == "list":
			return list_config.sections()
		else:
			raise NoSuchItemException
	else:
		raise ConfDirUnsetException
		

# Can I get a L-E-G-A-C-Y on this one? It dies in the next commit.
#def get_path(path):
	#location = open(path)
	#log = location.read()
	#log = '<br /><em>%s</em><br />%s' % (path,log)
	#return log

def get_log(path_to_file):
	log = None
	fileobj = open ( path_to_file, 'r' )
	file = fileobj.read()
	return file

def add_final(text):
	global final
	finale = final
	final = '%s\n\n%s'%(finale,text)
	return final

def get_final():
	global final
	return final

def send_curl (logs, message = message, email = email):

	if module_path == None:
		print "send_curl : No output modules found, cannot continue."
		sys.exit(1)
	else:
		execfile(module_path)
	