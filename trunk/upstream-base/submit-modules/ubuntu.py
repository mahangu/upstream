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

module_name = "ubuntu"
module_description = """Module for paste.ubuntu-nl.org"""
module_submit_url = "http://paste.ubuntu-nl.org/"


def execute(submit_name, submit_message, log_tuple):
	global module_submit_url
	
	contents = submit_name + "\n" + fill(submit_message) + flat_log(log_tuple)

	# bypassing "anti-spam"
	hashcash = urlopen("http://paste.ubuntu-nl.org/hashcash/").read().rstrip('\n')

	# 'poster' cannot exceed 21 characters for paste.ubuntu-nl.org
	# wrapping submit_message only at the moment to the default characters
	post_data = {'content': contents, 'poster': "Upstream", 'syntax': "text", 'hashcash_value': hashcash}

	# Send the data
	try:
		paste = urlopen(module_submit_url, urlencode(post_data))
	except IOError:
		return (False, "I/O Error")
	

	result_url = paste.geturl()
	result_xml = paste.read()

	# TODO implement some error checking before reporting success.
	# Now partially implemented, see above.  We still have to do more
	# parsing to see if we actually got a paste in

	return (True, result_url)
