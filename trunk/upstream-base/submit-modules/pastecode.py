#!/usr/bin/python
#
# Upstream pastebin.com  module.
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


from util import flat_log
from urllib import urlopen, urlencode

module_name = "pastecode"
module_description = """Module for pastecode.com"""
module_submit_url = "http://pastecode.com"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url

	contents = submit_name + "\n\n" + submit_message + "\n\n" + flat_log(log_tuple)

	# 'expiry' specifies for what period of time the paste should be kept
	#	"d" - one day
	#	"m" - one month (this is default on the web interface)
	#	"f" - forever
	post_data = { 'format' : "text", 'code2': contents, 'poster': "Upstream", 'paste': "Send", 'expiry': "m" }

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return (False, "I/O Error")

	result_url = paste.geturl()
	result_xml = paste.read()

	if not (result_url.startswith("http://pastecode.com/") and result_url[21:].isdigit()):
		return (False, "Did not return a proper url.")

	return (True, result_url)
