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

COLL_LFLAG = 0
COLL_SFLAG = 1
COLL_PATH = 2

class LogModuleDescrCollisionException(Exception):
	def __init__(self, col_type, attr):
		self.col_type = col_type
		self.attr = attr
	def __repr__(self):
		return "raised LogModuleDescCollisionException(" + self.col_type + ")"
	def __str__(self):
		if self.col_type == COLL_LFLAG:
			return "Log Modules Collided: multiple long flag %s" % self.attr
		elif self.col_type == COLL_SFLAG:
			return "Log Modules Collided: multiple short flag %s" % self.attr
		elif self.col_type == COLL_PATH:
			return "Log Modules Collided: multiple path %s" % self.attr
		else:
			return "Log Modules Collided: unknown reason"

# Log modules should do whatever they feel like and return a tuple of the form
# ( logname, logcontents )

class LogModule(moduleloader.LoadedModule):
	def __init__(self, module, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.LoadedModule.__init__(self, module, fault_tolerance, debug_output)
		self.log_path = self.module.log_path
		self.short_flag = self.module.short_flag
		self.long_flag = self.module.long_flag		
	def execute(self):
		try:
   			res =  self.module.execute()
   			if type(res) != tuple:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
   					print "Incorrect returned object, expected tuple"
   				if self.fault_tolerance:
   					return "Error in module loader %s : %s " % (self.module_name, self.module_log_path), "Error"
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
   					print "Sucess loading log"
   				return res
   			
    		except:
    			if self.debug_output >= moduleloader.DEBUG_ALL:
    				print "Error in execution of %s" % self.module_name
    				print sys.exc_info()[0]
    				
    			if self.fault_tolerance:
   				formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
   				return "Error in module loader %s : %s " % (self.module_name, self.module_log_path), "Error"
   			else:
   				raise

class LogModuleLoader(moduleloader.ModuleLoader):
	necessary_attributes = moduleloader.ModuleLoader.necessary_attributes + ["log_path", "short_flag", "long_flag"]
	necessary_attr_types = moduleloader.ModuleLoader.necessary_attr_types + [str, str, 
	ModuleWrapper = LogModule
	used_short_flags = []
	used_long_flags = []
	used_paths = []
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output)
		
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
			else:
				raise LogModuleDescrCollisionException(COLL_PATH, module.log_path)
			
		if self.debug_output >= moduleloader.DEBUG_ALL:
			print "Module short flag (%s) does not already exist: %s" % (module.short_flag, not module.short_flag in self.used_short_flags)	
		if module.short_flag in self.used_short_flags:
			if self.fault_tolerance:
				return  False	
			else:
				raise LogModuleDescrCollisionException(COLL_SFLAG, module.short_flag)	
				
		if self.debug_output >= moduleloader.DEBUG_ALL:
			print "Module long flag (%s) does not already exist: %s" % (module.long_flag, not module.long_flag in self.used_long_flags)	
		if module.long_flag in self.used_long_flags:
			if self.fault_tolerance:
				return  False	
			else:
				raise LogModuleDescrCollisionException(COLL_LFLAG, module.long_flag)
			
		# Add all these to the already used list
		self.used_long_flags.append(module.long_flag)
		self.used_short_flags.append(module.short_flag)
		self.used_paths.append(module.log_path)	
		
		return True	
