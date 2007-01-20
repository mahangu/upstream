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
class SubmitPlugin(threading.Thread):
	func_ptr_list = []
	def __init__(self, message_buffer):
		threading.Thread.__init__(self)
		self.m_buffer = message_buffer
		if self.__class__.run != SubmitPlugin.run:
			self.m_buffer.backendSendMessage((messageframe.DONE_ERROR, "Malformed submit module"))
	def run(self):
		try:
			self.execute()
		except Exception, e:
			self.m_buffer.backendSendMessage((messageframe.DONE_ERROR, "Unhandled exception in the plugin object:\n%s" % e))
			
	def execute(self):
		abstract()

class SubmitModule(moduleloader.LoadedModule):
	def __init__(self, module, trust_level, fault_tolerance, debug_level):
		moduleloader.LoadedModule.__init__(self, module, trust_level, fault_tolerance, debug_level)
		self.module_submit_url = self.module.module_submit_url
		self._message_buffer = messageframe.MessageBuffer()
		
		
	def getBuffer(self):
		return self._message_buffer
	
	def execute(self):
		try:
			self.plugin = self.module.createSubmit(self._message_buffer)
		except Exception, e:
			self._message_buffer.backendSendMessage((messageframe.DONE_ERROR, "Could not instantiate plugin object:\n%s" % e))
		else:
			self.plugin.setDaemon(True)
			try:
				self.plugin.start()
			except Exception, e:
				self._message_buffer.backendSendMessage((messageframe.DONE_ERROR, " Unhandled exception in the plugin object:\n%s" % e))
			

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
