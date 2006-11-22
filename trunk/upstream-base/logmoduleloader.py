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

import moduleloader, sys, threading, time

# Log modules should do whatever they feel like and return a tuple of the form
# ( logname, logcontents )

class LogModule(moduleloader.LoadedModule):
	def __init__(self, module, trust_level, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.LoadedModule.__init__(self, module, trust_level, fault_tolerance, debug_output)
		self.log_path = self.module.log_path
		self.category = self.module.category
		self.previous_load = False
			
	def execute(self):		
		self.previous_load = True
		try:
			self.result =  self.module.execute()
			if not isinstance(self.result, tuple) or len(self.result) != 2:
				if self.debug_output >= moduleloader.DEBUG_ALL:
					print "Incorrect return from module"
				return "Error in module loader %s: %s " % (self.module_name, self.log_path), "Incorrect return type"
			else:
				if self.debug_output >= moduleloader.DEBUG_ALL:
					print "Success loading log %s: %s" % (self.module_name, self.log_path)
				return self.result
			
		except:
			if self.debug_output >= moduleloader.DEBUG_ALL:
				print "Error in execution of %s" % self.module_name
				print sys.exc_info()[0]
				
			if self.fault_tolerance:
				self.result = "Error in module loader %s: %s " % (self.module_name, self.log_path), "Error"
				return self.result
			else:
				raise
		
			
				
	
	# If used complete hander should be of type method(result, user_data)
	def executeThreaded(self, complete_handler = None, user_data = None):
		self.complete_handler = complete_handler
		self.user_data = user_data
		self.start()
		
	def run(self):
		self.execute()
		if self.complete_handler:
			self.complete_handler(self.result, self.user_data)
			
	def getResult(self):
		return self.result

class LogValidator(moduleloader.GenericValidator):
	necessary_attributes = moduleloader.GenericValidator.necessary_attributes + ["log_path", "category"]
	necessary_attr_types = moduleloader.GenericValidator.necessary_attr_types + [str, list]
	ModuleWrapper = LogModule
	def __init__(self, parent, plugin_conf, fault_tolerance, debug_output):
		moduleloader.GenericValidator.__init__(self, parent, plugin_conf, fault_tolerance, debug_output)
			
	def validate_additional(self, module):
		return self.validate_execution_hook(module, "execute", 0) and self.validate_category_contains_str(module)
	
	def validate_category_contains_str(self, module):
		for field in module.category:
			if self.debug_output >= moduleloader.DEBUG_ALL:
				print "%s is of type str: %s" % (field, isinstance(field, str)) 
			if not isinstance(field, str):
				return False
		return True
		
class LogGrouper(threading.Thread):
	def __init__(self, parent, debug_output):
		threading.Thread.__init__(self)
		self.parent = parent
		self.debug_output = debug_output
				
	def run(self):
		if self.parent.debug_output >= moduleloader.DEBUG_ALL:
			print "Module validator pool size: %d" % self.parent.valid_running
			
		while self.parent.valid_running > 0 or self.parent.group_status < self.parent.total_loaded_mod:
			self.parent.group_pool_lock.acquire()
			if self.parent.group_status < self.parent.total_loaded_mod:
					
				mod = self.parent.valid_modules[self.parent.group_status]
				self.parent.group_status = self.parent.group_status + 1
				self.parent.group_pool_lock.release()
		
				
				if self.parent.debug_output >= moduleloader.DEBUG_ALL:
					print "Grouping: %s with category %s" % (mod, mod.category)
				for cat in mod.category:
					if not cat in self.parent.module_groupings:
						if self.parent.debug_output >= moduleloader.DEBUG_ALL:
							print "Group %s not found, adding" % cat
							
						self.parent.dict_lock.acquire()
						self.parent.module_groupings[cat] = [mod]
						self.parent.dict_lock.release()
						
					else:
						if self.parent.debug_output >= moduleloader.DEBUG_ALL:
							print "Group %s found, appending" % mod.category
							
						self.parent.dict_lock.acquire()
						self.parent.module_groupings[cat].append(mod)
						self.parent.dict_lock.release()
				
			else :
				self.parent.group_pool_lock.release()
				time.sleep(0.01)							
		
		self.parent.group_pool_lock.acquire()		
		self.parent.group_running = self.parent.group_running - 1
		self.parent.group_pool_lock.release()

class LogModuleLoader(moduleloader.ModuleLoader):
	ValidatorClass = LogValidator
	
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE, thread_pool_size=moduleloader.THREAD_POOL_MAX, group_pool_size=moduleloader.THREAD_POOL_MAX):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output, thread_pool_size)
		self.group_pool_size = group_pool_size
		self.module_groupings = dict()
		self.dict_lock = threading.Lock()
		self.group_pool_lock = threading.Lock()
		self.group_running = 0
		self.group_pool = []
		self.group_status = 0
	
		for x in range(0, self.group_pool_size):
			log_thread = LogGrouper(self, self.debug_output)
			self.group_pool_lock.acquire()
			self.group_running = self.group_running + 1
			self.group_pool.append(log_thread)
			self.group_pool_lock.release()
			
			log_thread.start()
	
		
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
			
	def getGroupCompleteRatio(self):
		if self.total_found_mod:
			return (self.group_status + 0.0)/self.total_found_mod
		else:
			return 0
			
	def join(self):
		moduleloader.ModuleLoader.join(self)
		for x in self.group_pool:
			x.join()
		if self.debug_output >= moduleloader.DEBUG_ALL and self.group_running > 0:
			print "ERROR: group worker crashed!"
	
	
