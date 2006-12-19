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


TYPE_STR = 0
# For passwords
TYPE_SECRET_STR = 1
TYPE_SELECT = 2
TYPE_MULTISELECT = 3
TYPE_TOGGLE = 4
TYPE_LOG = 5


REQUEST = 1
INFORMATION = 0
ERROR = 2
DONE = 3

# Messages shall be of the form
# ( TYPE , RELEVANT_DATA)
# If TYPE is Information, Error or Done, there should be a human
# readable string contained as RELEVANT_DATA
# If TYPE is a request, it should contain a list of tuples of the form
# (FIELD_TYPE, FIELD_NAME, ADDITIONAL_INFOMATION)
# ADDITIONAL INFORMATION can be interpreted several ways
# for instance, a string field might contain a default string, or a
# request for a "selection" would contain a list of choices
# Requests will be answered in the order they were sent out as single
# objects
class MessageBuffer:
	def __init__(self):
		threading.Thread.__init__(self)
		self._back_to_front = Queue()
		self._front_to_back = Queue()
			
	def frontendSendMessage(message):
		self._front_to_back.put(message)
		
	def frontendMessageWaiting():
		return self._back_to_front.qsize() > 0
		
	def frontendReceiveMessage():
		return self._back_to_front.get(true)
		
	def backendSendMessage(message):
		self._back_to_front.put(message)
	
	def backendMessageWaiting():
		return self._front_to_back.qsize() > 0
		
	def backendReceiveMessage():
		return self._front_to_back.get(true)
	
