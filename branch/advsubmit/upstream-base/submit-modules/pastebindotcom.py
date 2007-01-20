#!/usr/bin/python
#
# Upstream pastebin.com  module.
# Copyright (C) 2006  Jason Ribeiro <jason.ribeiro@gmail.com>,
# Ryan Zeigler <zeiglerr@gmail.com>
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
import messageframe
from urllib import urlopen, urlencode

module_name = "pastebindotcom"
module_description = """Module for pastebin.com"""
module_submit_url = "http://pastebin.com"

def createSubmit(m_buffer):
	return PastebindotcomPlugin(m_buffer)	
	
class PastebindotcomPlugin(submitmoduleloader.SubmitPlugin):
	module_submit_url = module_submit_url
	def __init__(self, m_buffer):
		submitmoduleloader.SubmitPlugin.__init__(self, m_buffer)
		
	def execute(self):
		# Batch all messages that we know we need.
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_UID,) )
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_LOGS,) ) 
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_DESCR,) )		
		
		uid = self.m_buffer.backendReceiveMessage()
		logs = self.m_buffer.backendReceiveMessage()
		problem_description = self.m_buffer.backendReceiveMessage()
		flat_log_type = ""
		for log in logs:
			flat_log_type = flat_log_type + "\n%s:\n\n%s" % (log, logs[log])
		# 'expiry' specifies for what period of time the paste should be kept
		#	"d" - one day
		#	"m" - one month (this is default on the web interface)
		#	"f" - forever
		post_data = { 'format' : "text", 'code2': uid + "\n\n" + problem_description + "\n\n" + flat_log_type, 'poster': "Upstream", 'paste': "Send", 'expiry': "m" }
		# IOErrors are caught by the enclosing block, one shot attempt
		paste = urlopen(self.module_submit_url, urlencode(post_data))
		result_url = paste.geturl()
		# This may not longer be necessary
		result_xml = paste.read()	
		print result_url	
		# TODO: some kind of error checking
		self.m_buffer.backendSendMessage( (messageframe.DONE, result_url, result_xml) )