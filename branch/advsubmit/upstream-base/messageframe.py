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

import threading
import submitmoduleloader

class Message:
	def __init__(self, title, content):
		self._title = title
		self._content = content


class BadTypeException(Exception):
	def __init__(self, expected_type, received_type):
		Exception.__init__(self)
		self._expected_type = expected_type
		
	def __str__(self):
		return  "%s got bad type: %s" % (Exception.__str__(self), self._expected_type)

class MessageBuffer(threading.Thread):
	def __init__(self, submitter):
		threading.Thread.__init__(self)
		
		if not isinstance(submitter, submitmoduleloader.SubmitPlugin): 
			raise BadTypeException(submitmoduleloader.SubmitPlugin, type(submitter))
		
		self._back_to_front = Queue()
		self._front_to_back = Queue()
			
	def backPush(self, message):
		if isinstance(message):
			self._back_to_front.push(message)
		else:
			# Throw an exception that should bump us out any plugin
			# written code, unless the module is really, really malicious
			# and catches this exception.
			raise BadTypeException(Message, message.__class__)
	
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
		