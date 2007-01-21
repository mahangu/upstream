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
import dialog
from urllib import urlopen, urlencode

module_name = "Display Test"
module_description = """Module for exercising messaging functions"""
module_submit_url = "No submit url"

def createSubmit(m_buffer):
	return DisplaytestPlugin(m_buffer)	
	
class DisplaytestPlugin(submitmoduleloader.SubmitPlugin):
	module_submit_url = module_submit_url
	def __init__(self, m_buffer):
		submitmoduleloader.SubmitPlugin.__init__(self, m_buffer)
		
	def execute(self):
		# Batch all messages that we know we need.
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_UID,) )
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_LOGS,) ) 
		self.m_buffer.backendSendMessage( (messageframe.REQUEST_DESCR,) )
		self.m_buffer.backendSendMessage((messageframe.REQUEST_PW, True))
		self.m_buffer.backendSendMessage((messageframe.REQUEST_PW, False))
		self.m_buffer.backendSendMessage((messageframe.REQUEST_STRINGS, [("This is the first string", ""), ("This is the second string", "")]))	
		
		uid = self.m_buffer.backendReceiveMessage()
		logs = self.m_buffer.backendReceiveMessage()
		flat_log_type = ""
		for log in logs:
			flat_log_type = flat_log_type + "\n%s:\n\n%s" % (log, logs[log])
		problem_description = self.m_buffer.backendReceiveMessage()
		password_wuname = self.m_buffer.backendReceiveMessage()
		default_password = self.m_buffer.backendReceiveMessage()
		multiple_strings = self.m_buffer.backendReceiveMessage()
		
		d = dialog.Dialog()
		d.msgbox("The resulting uid was: " + uid)
		d.msgbox("Logs were received: " + flat_log_type)
		d.msgbox("Problem description received: " + problem_description)
		d.msgbox("Password received: " + password_wuname[0] + " Username: " + password_wuname[1])
		d.msgbox("Password received: " + default_password[0])
		for x in multiple_strings:
			d.msgbox("A string received was: " + x)
		
		self.m_buffer.backendSendMessage( (messageframe.DONE, "This is a completion message") )