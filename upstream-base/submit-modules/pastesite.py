#!/usr/bin/python
#
# Upstream pastesite.com  module.
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


from util import flat_log
from urllib import urlopen, urlencode
import re

module_name = "pastesite"
module_description = """Module for http://pastesite.com/"""
module_submit_url = "http://pastesite.com/new"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url

	contents = submit_name + "\n\n\n" + submit_message + "\n\n\n" + flat_log(log_tuple)

	post_data = { 'paste': contents, 'type': "0", 'lifetime': "1" }

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return (False, "I/O Error")

	result_xml = paste.read()

	result_url = paste.geturl()
	# TODO: We need to check that the page we get back actually has the logs

	return (True, result_url)
