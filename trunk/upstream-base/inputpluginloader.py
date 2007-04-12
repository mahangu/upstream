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

REQUIRED_FIELDS = [("category", list), ("log_path", str)]

class InputPlugin(pluginloader.Plugin):
	def __init__(self, plugin, trust_lvl):
		pluginloader.Plugin.__init__(self, plugin, trust_lvl)
		self.log_path = self.getPlugin().log_path
	def get_category(self):
		return self.getPlugin().category
	
	def execute(self):
		return self.execute_plugin()
	
	def execute_plugin(self):
		try:
			return self.getPlugin().execute()
		except Exception, e:
			return "Invokation terminated with exception:\n\t%s\n" % e

class InputPluginLoader(pluginloader.PluginLoader):
	# Initialize an area with ungrouped things
	
	def __init__(self, config, output_sync):
		pluginloader.PluginLoader.__init__(self, config, output_sync)
		self.__prior_used_paths = []
		self.__plugin_groups = dict()
		self.__grouping_complete = threading.Event()
		self.__group_queue = Queue.Queue()
		self.__grouped_plugin_count = 0
	
	def run(self):
		pluginloader.PluginLoader.run(self)
		self.__groupAll__()
		
	def getCategories(self):
		return [category for category in self.__plugin_groups]
	
	def getInCategory(self, cat_name):
		try:
			return self.__plugin_groups[cat_name]
		except Exception, e:
			return None
	
	def getUniqueInCategories(self, category_list):
		plugins = []
		for category in category_list:
			try:
				for obj in self.__plugin_groups[category]:
					if obj not in plugins:
						plugins.append(obj)
			except Exception, e:
				pass
		return plugins
				
	def waitGroupingComplete(self):
		self.__grouping_complete.wait()
		
	def groupingIsComplete(self):
		return self.__grouping_complete.isSet()
	
	def getCompleteFrac(self):
		p_frac = pluginloader.PluginLoader.getCompleteFrac(self)
		valid_pc = self.getValidPluginCount()
		if valid_pc == 0:
			valid_pc = 1
		gplugin_c = self.__grouped_plugin_count
		return (p_frac + (gplugin_c + 0.0)/valid_pc)/2
		
	def getGroupingCount(self):
		return self.__grouped_plugin_count
		
	def __setGroupingComplete__(self):
		# Set the progress changed as well.
		self.__grouping_complete.set()
		self.__setProgressChanged__()
		
	def __isValidated__(self, plugin, pvl_id):
		plugin_obj = InputPlugin(plugin, self.__md5Verify__(plugin, pvl_id))
		self.__addValidPlugin__(plugin_obj)
		self.__setToGroup__(plugin_obj)
		self.__prior_used_paths.append(plugin.log_path)
		
	def __setToGroup__(self, plugin):
		self.__group_queue.put(plugin)
		
	def __hasNextToGroup__(self):
		return not self.__group_queue.empty()
	
	def __getNextToGroup__(self):
		return self.__group_queue.get_nowait()
	
	def __validPlugin__(self, plugin, pvl_id):
		super = pluginloader.PluginLoader.__validPlugin__(self, plugin, pvl_id)
		has_categories = self.__validate_fields__(plugin, REQUIRED_FIELDS, True, pvl_id)
		has_func = self.__validate_function__(plugin, "execute", 0, pvl_id)
		collision = self.__logPathCollision(plugin)		
		return super and has_categories and has_func and not collision
	
	def __logPathCollision(self, plugin):
		return plugin.log_path in self.__prior_used_paths
	
	def __groupAll__(self):
		gl_id = self.__newOstream__("Grouping Log")
		while self.__hasNextToGroup__():
			plugin_obj = self.__getNextToGroup__()
			self.__group__(plugin_obj, gl_id)
		self.__setGroupingComplete__()
		
	def __group__(self, plugin_obj, s_id):
		for cat in plugin_obj.get_category():
			if cat in self.__plugin_groups and type(cat) == str:
				self.__writeOstream__(s_id, "Adding plugin %s to category %s.\n" % (plugin_obj, cat))
				self.__plugin_groups[cat].append(plugin_obj)
			elif type(cat) == str:
				self.__writeOstream__(s_id, "Adding plugin %s to new category %s.\n" % (plugin_obj, cat))
				self.__plugin_groups[cat] = [plugin_obj]
			else:
				self.__writeOstream__(s_id, "Plugin %s had a non-string category.\n" % plugin_obj)
		self.__grouped_plugin_count = self.__grouped_plugin_count + 1
		self.__setProgressChanged__()

# vim:set noexpandtab: 
