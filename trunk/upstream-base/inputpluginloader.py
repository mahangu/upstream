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

import pluginloader, moduleloader, sys, threading, time, Queue

# Log modules should do whatever they feel like and return a string
# containing the log contents

REQUIRED_FIELDS = [("category", list)]

class InputPlugin(pluginloader.Plugin):
	def __init__(self, plugin, trust_lvl):
		pluginloader.Plugin.__init__(self, plugin, trust_lvl)
		
	def get_category(self):
		return self.get_plugin().category
	
	def execute_plugin(self):
		return self.get_plugin().execute()

class InputPluginLoader(pluginloader.PluginLoader):
	__plugin_groups = dict()
	__grouping_complete = threading.Event()
	__group_queue = Queue.Queue()
	__grouped_plugin_count = 0
	def __init__(self, config, output_sync):
		pluginloader.PluginLoader.__init__(self, config, output_sync)
	
	def run(self):
		pluginloader.PluginLoader.run(self)
		self.__group_all__()
		
	def get_categories(self):
		return [category for category in self.__plugin_groups]
	
	def get_in_category(self, cat_name):
		try:
			return self.__plugin_groups[cat_name]
		except Exception, e:
			return None
	
	def get_unique_in_categories(self, category_list):
		plugins = []
		for category in category_list:
			try:
				for obj in self.__plugin_groups[category]:
					if obj not in plugins:
						plugins.append(obj)
			except Exception, e:
				pass
		return plugins
					
	def dump_dict(self):
		print self.__plugin_groups
				
	def wait_grouping_complete(self):
		self.__grouping_complete.wait()
		
	def __set_grouping_complete__(self):
		self.__grouping_complete.set()
		
	def __set_validated__(self, plugin, pvl_id):
		plugin_obj = InputPlugin(plugin, self.__md5_verify__(plugin, pvl_id))
		self.__add_valid_plugin__(plugin_obj)
		self.__set_to_group__(plugin_obj)
		
	def __set_to_group__(self, plugin):
		self.__group_queue.put(plugin)
		
	def __has_next_to_group__(self):
		return not self.__group_queue.empty()
	
	def __get_next_to_group__(self):
		return self.__group_queue.get_nowait()
	
	def __valid_plugin__(self, plugin, pvl_id):
		super = pluginloader.PluginLoader.__valid_plugin__(self, plugin, pvl_id)
		has_categories = self.__validate_fields__(plugin, REQUIRED_FIELDS, True, pvl_id)
		has_func = self.__validate_function__(plugin, "execute", 0, pvl_id)
		return super and has_categories and has_func
	
	def __group_all__(self):
		gl_id = self.__new_ostream__("Grouping Log")
		while self.__has_next_to_group__():
			plugin_obj = self.__get_next_to_group__()
			self.__group__(plugin_obj, gl_id)
		self.__set_grouping_complete__()
		
	def __group__(self, plugin_obj, s_id):
		for cat in plugin_obj.get_category():
			if cat in self.__plugin_groups:
				self.__write_ostream__(s_id, "Adding plugin %s to category %s.\n" % (plugin_obj, repr(cat)))
				self.__plugin_groups[cat].append(plugin_obj)
			else:
				self.__write_ostream__(s_id, "Adding plugin %s to new category %s.\n" % (plugin_obj, repr(cat)))
				self.__plugin_groups[cat] = [plugin_obj]
		self.__grouped_plugin_count = self.__grouped_plugin_count + 1
		self.__set_progress_changed__()
		
	

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
			if not isinstance(self.result, str):
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
		while self.parent.aliveValidator() or self.parent.group_status < self.parent.total_loaded_mod:
			self.parent.group_pool_lock.acquire()
			if self.parent.group_status < self.parent.total_loaded_mod:
					
				mod = self.parent.valid_modules[self.parent.group_status]
				self.parent.group_status = self.parent.group_status + 1
				self.parent.group_pool_lock.release()
				if self.debug_output >= moduleloader.DEBUG_ALL:
					print "Grouping module %s" % mod
				for cat in mod.category:
					if not cat in self.parent.module_groupings:
						if self.parent.debug_output >= moduleloader.DEBUG_ALL:
							print " Group %s not found, adding" % cat
							
						self.parent.dict_lock.acquire()
						self.parent.module_groupings[cat] = [mod]
						self.parent.dict_lock.release()
						
					else:
						if self.parent.debug_output >= moduleloader.DEBUG_ALL:
							print " Group %s found, appending" % mod.category
							
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
			return None
		
	def getUniqueModulesInCategories(self, list_of_cat):
		ret_mods = []
		for category in list_of_cat:
			for mod in self.getModulesInCategory(category):
				if not mod in ret_mods:
					ret_mods.append(mod)
		return ret_mods
		
	def getCategories(self):
		if self.module_groupings:
			return [category for category in self.module_groupings]
		else:
			return None
			
	def getGroupCompleteRatio(self):
		if self.total_found_mod:
			return (self.group_status + 0.0)/self.total_found_mod
		else:
			return 0
			
	def loadAdditionalModules(self, full_path_list):
			if moduleloader.ModuleLoader.loadAdditionalModules(full_path_list):
				for x in range(0, self.group_pool_size):
					log_thread = LogGrouper(self, self.debug_output)
					self.group_pool_lock.acquire()
					self.group_running = self.group_running + 1
					self.group_pool.append(log_thread)
					self.group_pool_lock.release()					
					log_thread.start()					
				return True
			else:
				return False
			
	def join(self):
		moduleloader.ModuleLoader.join(self)
		for x in self.group_pool:
			x.join()
		if self.debug_output >= moduleloader.DEBUG_ALL and self.group_running > 0:
			print "ERROR: one or more group workers crashed!"
	
	
