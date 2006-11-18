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

FIELD_TYPES = ("string", "password", "selection", "toggle")
MESSAGE_TYPES = ("information", "error", "request")		

class Message:
	def __init__(self, m_type, title, message):
		self._m_type = m_type
		self._title = title
		self._message = message
		
	def getm_type(self): return self._m_type
	def gettitle(self): return self._title
	def getmessage(self): return self._message
		
class Request(Message):
	def __init__(self, title, message):
		Message.__init__(self, MESSAGE_TYPES[2], title, message)
		
		
