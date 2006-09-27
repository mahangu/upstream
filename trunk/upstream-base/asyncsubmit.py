#!/usr/bin/python
#
# upstream  log file aggregator and report tool for *nix systems.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.\
# A class to handle running of requests

import threading
import functions

class ThreadSubmit(threading.Thread):
	def __init__(self, email, support, support_type):
		threading.Thread.__init__(self)
		self.email = email
		self.support = support
		self.support_type = support_type
		# These store useful variables for the class
		self.is_started = False
		self.result = None
		self.func_handler = None
		self.func_handler_data = None
	# Func handler should be of the form func_handler(py_curl_result, user_data)
	# func_handler_data will be passed into the function as user data
	def set_complete_handler(self, func_handler, func_handler_data=None):
		self.func_handler = func_handler
		self.func_handler_data = func_handler_data
	
	# Determine if the thread has started yet
	def isStarted(self):
		return self.is_started
	
	# Get the result returned by whatever the current submit method is
	def get_result(self):
		return self.result
		
	def run(self):
		# First thing, we must start the thread
		self.is_started = True
		for section in self.support_type:
			command = functions.get_conf_item("list", section, "command")
			dump = functions.get_dump(command)
			response = functions.add_final(dump)
		user_logs = functions.get_final()
		self.result = functions.send_curl(user_logs, self.support, self.email)
		if self.func_handler:
			self.func_handler(self.result, self.func_handler_data)
