#!/usr/bin/python
#
# Upstream paste.redkrieg.com  module.
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


import submitmoduleloader
from util import flat_log
import webbrowser, os

module_name = "red"
module_description = """Module for Redkrieg's pastebin. Much <3 to him for hosting us."""
module_submit_url = "http://pastebin.redkrieg.com?page=submit"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url
	
	
	print "Executing"
	
	flat_log_type = flat_log(log_tuple)
	flat_log_type = flat_log_type.replace("\"","")
	contents = submit_message + flat_log_type
	
	referer= "http://pastebin.redkrieg.com"
	# misc= "&channel=none&colorize=none"
	
	# Prepare Curl object
	import pycurl
	from urllib import urlencode
	from StringIO import StringIO
	c = pycurl.Curl()
	c.setopt(pycurl.URL, module_submit_url)
	c.setopt(pycurl.POST, 1)
	post_data = { 'subject': "Upstream<%s>"%submit_name, 'language': "1", 'code': contents, 'nickname': "Upstream" }
	c.setopt(pycurl.POSTFIELDS, urlencode(post_data))
	c.setopt(pycurl.REFERER, referer)
	clog = StringIO()
	c.setopt(pycurl.WRITEFUNCTION, clog.write)
	c.perform()
	
	#Do we need to generate this file anymore? --RedKrieg
	#No, killing it off
	#file = open ( 'red.html', 'w' )
	
	foo = clog.getvalue()
	
	#file.write ( "%s"%(foo) )
	
	#file.close() 
	#End question --RedKrieg
	
	response_url = "http://pastebin.redkrieg.com/?page=view&id="+foo[foo.find("&id=")+4:foo.find("&id=")+14]	#get url of paste
	
	print response_url	#simple debug print
	
	# print clog.getvalue()
	
	# no, no error checking yet.
	return submitmoduleloader.SubmitModuleResult(True, True, foo, response_url)
