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



import pluginloader, threading, gettext
unknown_response = "The plugin returned an unintelligable response. This is a bug in the plugin."
exception_template = "The following exception occured: %s."

REQUIRED_FIELDS = [("module_submit_url", str)]

class OutputPlugin(pluginloader.Plugin):
	def __init__(self, plugin, trust_lvl):
		pluginloader.Plugin.__init__(self, plugin, trust_lvl)
		self.module_submit_url = self.getPlugin().module_submit_url
		
	def __process_result(self, result):
		if len(result) == 2 and type(result[1]) == str:
			return result
		else:
			return (False, unknown_response)
		
	def execute_plugin(self, s_name, s_message, log):	
		try:
			result = self.getPlugin().execute(s_name, s_message, log)
			return self.__process_result(result)
		except Exception, e:
			formatted_str = exception_template % (sys.exc_info()[0])
			self.result = (False, formatted_str)
			
	def execute(self, s_name, s_message, log):
		self.execute_plugin(s_name, s_message, log)
		
	def execute_threaded(self, s_name, s_message, log, complete_handler=None, user_data=None):
		self.__pluginThread = OutputPluginThreadWrapper(self.getPlugin(), s_name, s_message, log, complete_handler, user_data)
		self.__pluginThread.start()
		
	def wait_for_threaded_execute(self, timeout = 0):
		self.__pluginThread.plugin_complete.wait(timeout)
		
	def threaded_execute_is_running(self):
		return not self.__pluginThread.plugin_complete.isSet()
	
	def threaded_result(self):
		result = self.__pluginThread.get_result()
		return self.__process_result(result)
	
class OutputPluginThreadWrapper(threading.Thread):
	plugin_complete = threading.Event()
	def __init__(self, plugin, s_name, s_message, log, complete_handler, user_data):
		threading.Thread.__init__(self)
		self.__plugin = plugin
		self.__s_name_arg = s_name
		self.__s_message_arg = s_message
		self.__log_arg = log
		self.__complete_handler = complete_handler
		self.__user_data = None	
		
	def run(self):
		self.__result = self.__plugin.execute(self.__s_name_arg, self.__s_message_arg, self.__log_arg)
		if self.__complete_handler:
			self.__complete_handler(self.__result, self.__user_data)
		self.plugin_complete.set()
		
	def get_result(self):
		return self.__result

class OutputPluginLoader(pluginloader.PluginLoader):
	def __init__(self, config, output_sync):
		pluginloader.PluginLoader.__init__(self, config, output_sync)
		
	def __valid_plugin__(self, plugin, pvl_id):
		try:
			if pluginloader.PluginLoader.__valid_plugin__(self, plugin, pvl_id) and self.__validate_fields__(plugin, REQUIRED_FIELDS, True, pvl_id) and self.__validate_function__(plugin, "execute", 3, pvl_id):
				return True
		except Exception, e:
			self.__writeOstream__(pvl_id, "Validation failed with Exception:\n\t%s\n" % e)
		return False
		
	def __isValidated__(self, plugin, pvl_id):
		plugin_obj = OutputPlugin(plugin, self.__md5Verify__(plugin, pvl_id))
		self.__addValidPlugin__(plugin_obj)