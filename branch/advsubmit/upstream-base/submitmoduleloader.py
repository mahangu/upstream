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

import moduleloader, sys, messageframe, threading

# This is a class that all submit things should derive from
# Overriding the run() method generally shouldn't be done unless
# there is a really, really good reason
class SubmitPlugin(threading.Thread):
	func_ptr_list = []
	def __init__(self, message_buffer):
		self._m_buffer = message_buffer
		
	def run(self):
		try:
			for func_ptr in self.func_ptr_list
				func_ptr()
				if self.terminate:
					# Send some kind of failure message?
					break
				else:
					# Send some kind of message about state?
					pass
				
		except Error, e:
			# Send a failure message, because in this case, either a message
			# followed invalid format, or something crashed in the module itself
			pass
			

class SubmitModule(moduleloader.LoadedModule):
	def __init__(self, module, trust_level, fault_tolerance, debug_level):
		moduleloader.LoadedModule(module, trust_level, fault_tolerance, debug_level)
		self.module_submit_url = self.module.module_submit_url
		self.message_buffer = MessageBuffer()
		self.plugin = self.module.createSubmit(self.message_buffer)
		
	def getBuffer(self):
		return self.message_buffer
	
	def execute(self):
		self.plugin.start()

class SubmitValidator(moduleloader.GenericValidator):
	necessary_attributes = moduleloader.GenericValidator.necessary_attributes + ["module_submit_url"]
	necessary_attr_types = moduleloader.GenericValidator.necessary_attr_types + [str]
	ModuleWrapper = SubmitModule
	def __init__(self, parent, plugin_conf, fault_tolerance, debug_output):
		moduleloader.GenericValidator.__init__(self, parent, plugin_conf, fault_tolerance, debug_output)
	
	def validate_additional(self, module):
		valid_hook = self.validate_execution_hook(module, "createSubmit", 1)
		return valid_hook
			
class SubmitModuleLoader(moduleloader.ModuleLoader):
	ValidatorClass = SubmitValidator
	ModuleWrapper = SubmitModule
