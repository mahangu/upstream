#!/usr/bin/python
#
# Upstream pastebin.ca  module.
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
from urllib import urlopen, urlencode
import re

module_name = "pastebindotca"
module_description = """Module for pastebin.ca"""
module_submit_url = "http://pastebin.ca"


def execute(submit_email, submit_message, dict_of_logs):
	global module_submit_url
	
	print "Executing"

	# Put all the elements into one log
	flat_log_type = ""
	for log in dict_of_logs:
		flat_log_type = flat_log_type + "\n%s:\n\n%s" % (log, dict_of_logs[log])

	# TODO Are there any limits on these fields?
	# 'expiry' specifies for what period of time the paste should be kept:  No value means forever.
	# 'type': 1 means raw text
	post_data = { 'content': flat_log_type, 's': "Submit Post", 'description': submit_message, 'type': "1", 'expiry': "", 'name':  submit_email }

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return submitmoduleloader.SubmitModuleResult(True, False)

	# This is not the xml for the actual paste.
	# TODO See what we need to pass to SubmitModuleResult
	result_xml = paste.read()

	# Use regex to find the url
	match = re.search(r'<meta http-equiv="refresh" content=".+?(http://pastebin\.ca/\d+?)"', result_xml)
	if match:
		result_url = match.group(1)
	else:
		return submitmoduleloader.SubmitModuleResult(True, False)

	print result_url

	# TODO: We need to check that the page we get back actually has the logs

	return submitmoduleloader.SubmitModuleResult(True, True, result_xml, result_url)
