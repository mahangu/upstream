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



from util import flat_log
from urllib import urlopen, urlencode
from textwrap import fill

module_name = "rafb"
module_description = """Module for www.rafb.net"""
module_submit_url = "http://www.rafb.net/paste/paste.php"


def execute(nickname, submit_message, log_tuple):
	global module_submit_url

	contents = fill(submit_message) + flat_log(log_tuple)

	# wrapping submit_message to the default width (70)
	# 'nick' is limited to 30 characters
	# 'desc' is limited to 50 characters
	short_nickname = nickname[:30]
	post_data = { 'lang': "Plain Text", 'nick': short_nickname, 'desc': "", 'cvt_tabs': "No", 'text': contents}

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return (False, "I/O Error"

	result_url = paste.geturl()
	result_xml = paste.read()
	
	if not (result_url.startswith("http://rafb.net/p/") and 
			'/' not in result_url[18:] and
			result_url.endswith(".html")):
		return (False, "Did not return a proper url.")

	return (True, result_url)
