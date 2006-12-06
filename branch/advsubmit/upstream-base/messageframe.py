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
		pass
	
	def backMessageAvailable(self):
		pass
		
	def backPull(self):
		pass
	
	def frontPush(self, message):
		pass
	
	def frontAvailable(self):
		pass
		
	def frontPull(self):
		pass
		