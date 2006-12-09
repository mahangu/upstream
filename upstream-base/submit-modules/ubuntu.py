#!/usr/bin/python
#
# Upstream paste.ubuntu-nl.org  module.
# Copyright (C) 2006  Jason Ribeiro <jason.ribeiro@gmail.com>
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
from urllib import urlopen, urlencode
from textwrap import fill

module_name = "ubuntu"
module_description = """Module for paste.ubuntu-nl.org"""
module_submit_url = "http://paste.ubuntu-nl.org/"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url
	
	print "Executing"

	contents = submit_name + "\n" + fill(submit_message) + flat_log(log_tuple)

	# 'poster' cannot exceed 21 characters for paste.ubuntu-nl.org
	# wrapping submit_message only at the moment to the default characters
	post_data = { 'content': contents, 'poster': "Upstream", 'submit': "Paste it" }

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return submitmoduleloader.SubmitModuleResult(True, False)
	

	result_url = paste.geturl()
	result_xml = paste.read()

	print result_url

	# TODO implement some error checking before reporting success.
	# Now partially implemented, see above.  We still have to do more
	# parsing to see if we actually got a paste in

	return submitmoduleloader.SubmitModuleResult(True, True, result_xml, result_url)
