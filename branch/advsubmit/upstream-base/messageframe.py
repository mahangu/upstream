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

import getpass
import threading
import submitmoduleloader


TYPE_STR = 0
# For passwords
TYPE_SECRET_STR = 1
TYPE_SELECT = 2
TYPE_MULTISELECT = 3
TYPE_TOGGLE = 4
TYPE_LOG = 5


REQUEST = 0
INFORMATION = 1
ERROR = 2

class StatusUpdate:
	def __init__(self, current, total):
		self._cur = current
		self._tot = total
		
	def fpComplete(self):
		return (self._cur + 0.0)/self._tot

class Message:
	def __init__(self, title, content, m_type):
		self._title = title
		self._content = content
		self._m_type = m_type
		
	def title(self):
		return self._title
	
	def content(self):
		return self._content
	
	def getType(self):
		return self._m_type

# Done message indicates a successful completion
class DoneMessage(Message):
	def __init__(self, title, content):
		Message.__init__(self, title, content, INFORMATION)
		
# Error message indicates a some form of terminal error
# that the submission module doesn't think it can recover from
class ErrMessage(Message):
	def __init__(self, content):
		Message.__init__(self, "Error", content, ERROR)
	
class UndefinedRequest(Message):
	def __init__(self, title, message, req_descr):
		Message.__init__(self, title, message, REQUEST)
		# Perform validation on the request description
		if type(req_descr) != list:
			raise BadRequestException(self, "Not a list")
		# Further TODO: add some validation to make sure that types are matched
		for x in req_descr:
			if type(x) != tuple:
				raise BadRequestException(self, "List contains non-tuple")
			if len(x) != 3:
				raise BadRequestException(self, "Tuple is not of length 3")
			
		self._request_descr = req_descr
		self._reply = []
		for x in range(0, len(req_descr)):
			self._reply.append(None)
			
	def getRequestDescr(self):
		return self._request_descr
	
	def answerRequest(self, question, response):
		for x in self._request_descr:
			if x[0] == question:
				self._reply[self._request_descr.index(x)] = response
				break
	
	def getAnswer(self, question):
		for x in self._request_descr:
			if x[0] == question:
				return self._reply[self._request_descr.index(x)]
		
class AuthenticationRequest(UndefinedRequest):
	def __init__(self, content, use_pw_field):
		if use_pw_field:
			UndefinedRequest.__init__(self, "Authentication", content, [("Username", TYPE_STR, ""), ("Password", TYPE_SECRET_STR, "")])
		else:
			UndefinedRequest.__init__(self, "Authentication", content, [("Password", TYPE_SECRET_STR, "")])
			
	def answerUsername(self, un):
		self.answerRequest("Username", un)
		
	def answerPassword(self, pw):
		self.answerRequest("Password", pw)

class SubmitInfoRequest(UndefinedRequest):
	def __init__(self):
		UndefinedRequest.__init__("log", "log request", [("handle", TYPE_STR,  getpass.getuser()), ("logs", TYPE_LOG, None)]) 
		
	def answerLogs(self, logs):
		self.answerRequest("logs", logs)
		
	def answerUserHandle(self, handle):
		self.answerRequest("handle", handle)
		

class BadRequestException(Exception):
	def __init__(self, request, reason):
		Exception.__init__(self)
		self.request = request
		self.reason = reason
		
	def __str__(self):
		return "Type: %s was malformed: %s" % (type(self.request), self.reason)

class BadTypeException(Exception):
	def __init__(self, received_type):
		Exception.__init__(self)
		self._expected_type = expected_type
		
	def __str__(self):
		return  "%s got bad type: %s" % (Exception.__str__(self), self._expected_type)

class MessageBuffer:
	def __init__(self):
		threading.Thread.__init__(self)
		
		self._back_to_front = Queue()
		self._front_to_back = Queue()
			
	def backPush(self, message):
		if isinstance(message, Message) or isinstance(message, StatusUpdate):
			self._back_to_front.push(message)
		else:
			# Throw an exception that should bump us out any plugin
			# written code, unless the module is really, really malicious
			# and catches this exception.
			raise BadTypeException(message.__class__)
	
	def backMessageAvailable(self):
		return self._front_to_back.empty()
		
	def backPull(self):
		return self._front_to_back.get(True)
	
	def frontPush(self, message):
		self._front_to_push(message)
	
	def frontAvailable(self):
		return self._back_to_front.empty()
		
	def frontPull(self):
		return self._back_to_front.get(True)
		