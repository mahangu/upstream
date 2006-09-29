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
	# complete_handler should be of the form func_handler(SubmitModuleResult, user_data)
	# user_data may be arbitrary
	def __init__(self, submission_module, email, support_message, log_dict, complete_handler, complete_user_data):
		threading.Thread.__init__(self)
		self.submission_module = submission_module
		self.email = email
		self.support_message = support_message
		self.log_dict = log_dict
		self.complete_handler = complete_handler
		self.complete_user_data = complete_user_data
		
		self.is_started = False
		self.result = None
	
	# Determine if the thread has started yet
	def isStarted(self):
		return self.is_started
	
	# Get the result returned by whatever the current submit method is
	def get_result(self):
		return self.result
		
	def run(self):
		# First thing, we must start the thread
		self.is_started = True
		self.result = self.submission_module.execute(self.email, self.support_message, self.log_dict)
		self.complete_handler(self.result, self.complete_user_data)
				
