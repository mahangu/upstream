#!/usr/bin/python
#
# Upstream pastie.caboo.se  module.
# Copyright (C) 2006  Mahangu Weerasinghe <mahangu@gmail.com>
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
import re

module_name = "caboose"
module_description = """Module for pastie.caboo.se/"""
module_submit_url = "http://pastie.caboo.se/pastes/create"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url
	
	contents = submit_name + "\n\n\n" + submit_message + "\n\n\n" + flat_log(log_tuple)

	# TODO Are there any limits on these fields?
	# 'expiry' specifies for what period of time the paste should be kept:  No value means forever.
	# 'type': 1 means raw text
	post_data = { 'paste[parser]': "diff", 'paste[body]': contents, 'paste[authorization]': "burger", 'key': "" }

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return submitmoduleloader.SubmitModuleResult(True, False)

	# This is not the xml for the actual paste.
	# TODO See what we need to pass to SubmitModuleResult
	result_xml = paste.read()
	
	result_url = paste.geturl()

	# TODO: We need to check that the page we get back actually has the logs

	return submitmoduleloader.SubmitModuleResult(True, True, result_xml, result_url)
