#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Ryan Zeigler (zeiglerr@gmail.com)
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

import sys, threading, time


MESSAGE_TYPES = ("information", "error", "request")	
REQUEST_TYPES = ("undefined", "password", "log")	
FIELD_TYPES = ("string", "password", "selection", "toggle", "log")
		
class Message:
	def __init__(self, m_type, title, message):
				
		self._m_type = m_type
		self._title = title
		self._message = message
		
	def getm_type(self): return self._m_type
	def gettitle(self): return self._title
	def getmessage(self): return self._message
		
# A req field should be of type (field name, field type, field_add_data)
class UndefinedRequest(Message):
	def __init__(self, title, message, req_fields):
		Message.__init__(self, MESSAGE_TYPES[2], title, message, r_type = REQUEST_TYPES[0])
		# TODO: possible validation of req_fields?
		self.req_fields = req_fields
		self.ans_fields = [None for x in self.req_fields]
		self.request_type = r_type
		
	# Returns whether or not answering was successful
	def answerByName(self, name, answer):
		found = False
		for x in range(0, len(self.req_fields)):
			if self.req_fields[x][0] == name:
				found = True
				self.ans_fields[x] == answer
				
		return found
				
class PasswordRequest(UndefinedRequest):
	def __init__(self, title, message, req_uname):
		if req_uname:
			req_fields = [("Username", "string", None), ("Password", "password", None)]
		else:
			req_fields = [("Password", "password", None)]
			
		UndefinedRequest.__init__(self, title, message, req_fields)
		
	def hasUsername(self):
		for x in self.req_fields:
			if x[0] == "Username":
				return True
		return False
		
	def answerUsername(self, uname):
		return self.answerByName("Username", uname)
		
	def answerPassword(self, pword):
		return self.answerByName("Password", pword)
		
class LogRequest(UndefinedRequest):
	def __init__(self):
		UndefinedRequest.__init__("Log Request", "All your log are belong to us", ("log", "log", None))
		
	def answerLogs(self, log):
		return answerByName("log", log)
	
		
		
