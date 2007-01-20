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

import Queue

INFORMATION = 1
REQUEST_STRINGS = 2
REQUEST_UID = 3
REQUEST_LOGS = 4
REQUEST_DESCR = 5
REQUEST_PW = 6
DONE_ERROR = 7
DONE = 8

class MessageBuffer:
	def __init__(self):
		self._back_to_front = Queue.Queue()
		self._front_to_back = Queue.Queue()
			
	def frontendSendMessage(self, message):
		print message
		self._front_to_back.put(message)
		
	def frontendMessageWaiting(self):
		return self._back_to_front.qsize() > 0
		
	def frontendReceiveMessage(self):
		message = self._back_to_front.get(True)
		return message
		
	def backendSendMessage(self, message):
		self._back_to_front.put(message)
	
	def backendMessageWaiting(self):
		return self._front_to_back.qsize() > 0
		
	def backendReceiveMessage(self):
		return self._front_to_back.get(True)
	
