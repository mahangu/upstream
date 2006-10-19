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

import moduleloader, sys

# Log modules should do whatever they feel like and return a tuple of the form
# ( logname, logcontents )

class LogModule(moduleloader.LoadedModule):
	def __init__(self, module, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.LoadedModule.__init__(self, module, fault_tolerance, debug_output)
		self.log_path = self.module.log_path
		self.category = self.module.category
		# This is temporary to preserve backward compatability with old
		# code
		if self.module.short_flag:
			self.short_flag = self.module.short_flag
		else:
			self.short_flag = "-?"
			
		if self.module.long_flag:
			self.long_flag = self.module.long_flag
		else:
			self.long_flag = "--<?>"
			
	def execute(self):
		try:
   			res =  self.module.execute()
   			if type(res) != tuple:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
   					print "Incorrect returned object, expected tuple"
   				if self.fault_tolerance:
   					return "Error in module loader %s: %s " % (self.module_name, self.log_path), "Error"
   				else:
   					raise moduleloader.IncorrectModuleReturnException(type(res), type(SubmitModuleResult))
   			elif len(res) != 2:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
   					print "Incorrect number of items in returned tuple: module: %s" & self.name
   				if self.fault_tolerance:
   					return "Possible error in module loader %s: %s" % (self.module_name, res[0]), res[1]
   				else:
   					# I'm not sure what else to do here, perhaps another exception type?
   					raise moduleloader.IncorrectModuleReturnException(type(res), type(SubmitModuleResult))
   			else:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
					print "Success loading log %s: %s" % (self.module_name, self.log_path)
   				return res
   			
    		except:
    			if self.debug_output >= moduleloader.DEBUG_ALL:
    				print "Error in execution of %s" % self.module_name
    				print sys.exc_info()[0]
    				
    			if self.fault_tolerance:
   				formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
   				return "Error in module loader %s: %s " % (self.module_name, self.log_path), "Error"
   			else:
   				raise
			
	# If used complete hander should be of type method(result, user_data)
	def executeThreaded(self, complete_handler = None, user_data = None):
		self.email = email
		self.message = message
		self.log_dict = log_dict
		self.complete_handler = complete_handler
		self.user_data = user_data
		self.start()
		
	def run(self):
		self.result = self.execute()
		if self.complete_handler:
			self.complete_handler(self.result, self.user_data)
			
	def getResult(self):
		return self.result

class LogModuleLoader(moduleloader.ModuleLoader):
	necessary_attributes = moduleloader.ModuleLoader.necessary_attributes + ["log_path", "category"]
	necessary_attr_types = moduleloader.ModuleLoader.necessary_attr_types + [str, str]
	ModuleWrapper = LogModule
	used_paths = []
	module_groupings = None
	module_grouping_status = -1
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE, use_threading = False):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output, use_threading)
		# If we are using threading, we should do nothing, as we have
		# overriden the run method
		if not self.threaded:
			self.groupModules()
	
	def run(self):
		moduleloader.ModuleLoader.run(self)
		self.groupModules()
		
	def groupModules(self):
		self.module_grouping_status = 0.0
		counter = 0
		self.module_groupings = dict()
		for mod in self.valid_modules:
			if not mod.category in self.module_groupings:
				self.module_groupings[mod.category] = [mod]
			else:
				self.module_groupings[mod.category].append(mod)
			counter = counter + 1
			self.module_grouping_status = (counter + 0.0)/len(self.valid_modules)
		
	def getModulesInCategory(self, cat):
		if self.module_groupings:
			return self.module_groupings[cat]
		else:
			if self.debug_output >= moduleloader.DEBUG_ALL:
				print "Module Groupings aren't yet created (Thread inconsistency?)"
			return None
		
	def getCategories(self):
		if self.module_groupings:
			return [category for category in self.module_groupings]
		else:
			if self.debug_output >= moduleloader.DEBUG_ALL:
				print "Module Groupings aren't yet created (Thread inconsistency?)"
			return None
		
	def validate_additional(self, module):
		return self.validate_execution_hook(module, "execute", 0) and self.validate_non_duplicate_module_descr(module)
		
	# Validate to make sure we don't have colliding modules
	def validate_non_duplicate_module_descr(self, module):
		if self.debug_output >= moduleloader.DEBUG_ALL:
			print "Checking for module collisions"
		
		if self.debug_output >= moduleloader.DEBUG_ALL:
			print "Module log path (%s) does not already exist: %s" % (module.log_path, not module.log_path in self.used_paths)
		if module.log_path in self.used_paths:
			if self.fault_tolerance:
				return  False	
					
		# Add all these to the already used list
		self.used_paths.append(module.log_path)	
		
		return True	
