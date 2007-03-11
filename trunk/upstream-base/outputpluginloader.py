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



import pluginloader, threading

REQUIRED_FIELDS = [("module_submit_url", str)]

class OutputPlugin(pluginloader.Plugin):
	def __init__(self, plugin, trust_lvl):
		pluginloader.Plugin.__init__(self, plugin, trust_lvl)
		self.module_submit_url = self.get_plugin().module_submit_url
		
	def execute_plugin(self, s_name, s_message, log):	
		try:
			return self.get_plugin().execute(s_name, s_message, log)
		except Exception, e:
			formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
			self.result = SubmitModuleResult(False, False, formatted_str)
			
	def execute(self, s_name, s_message, log):
		self.execute_plugin(s_name, s_message, log)
		
	def execute_threaded(self, s_name, s_message, log, complete_handler=None, user_data=None):
		self.__pluginThread = OutputPluginThreadWrapper(self.get_plugin(), s_name, s_message, log, complete_handler, user_data)
		self.__pluginThread.start()
		
	def wait_for_threaded_execute(self, timeout = 0):
		self.__pluginThread.plugin_complete.wait(timeout)
		
	def threaded_execute_is_running(self):
		return not self.__pluginThread.plugin_complete.isSet()
	
	def threaded_result(self):
		return self.__pluginThread.get_result()
	
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
			self.__write_ostream__(pvl_id, "Validation failed with Exception:\n\t%s\n" % e)
		return False
		
	def __set_validated__(self, plugin, pvl_id):
		plugin_obj = OutputPlugin(plugin, self.__md5_verify__(plugin, pvl_id))
		self.__add_valid_plugin__(plugin_obj)


import moduleloader, sys

unknown_response = """<html>
				<head>
					<title>Error Page!</title>
				</head>
				<body>
					<h3>The module returned an unreconized type</h3><br />
					<p>This is usually due to an incorrectly designed
					submission module.  Your request may have succeeded,
					but we have way of determining this</p>
				</body>
			</html>"""

exception_template = """<html>
				<head>
					<title>Error Page!</title>
				</head>
				<body>
					<h3>An exception occured</h3><br />
					<p>The following exception: %s<br />
					occured while processing in module %s
					</p>
				</body>
			</html>"""

# This a type object that must be returned by all valid modules,
# we attempt to insulate the program code from errors such as this if said
# client code requests fault_tolerance, which is default
class SubmitModuleResult:
	def __init__(self, bool_ispaste, bool_success, result_xml=None, result_url=None):
		self.bool_ispaste = bool_ispaste
		self.bool_success = bool_success
		self.result_url = result_url
		self.result_xml = result_xml
		
class SubmitModule(moduleloader.LoadedModule):
	email = ""
	message = ""
	log_dict = ""
	def __init__(self, module, trust_level, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.LoadedModule.__init__(self, module, trust_level, fault_tolerance, debug_output)
		self.module_submit_url = self.module.module_submit_url
		
	def execute(self, email, message, log_dict):
		try:
   			res =  self.module.execute(email, message, log_dict)
   			# We are expecting a submit module result, take action if not found
			## We should consider:
			## http://www.python.org/download/releases/2.2.3/descrintro/
			## http://docs.python.org/ref/node33.html
   			#if type(res) == SubmitModuleResult:
   			if isinstance(res, SubmitModuleResult):
				self.result = res
   				return res
   			else:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
   					print "Module execute returned type %s expected %s" % (type(res), SubmitModuleResult)
   				if self.fault_tolerance:
   				 # We are using fault tolerance so try and send back a message to the user
				 	self.result = SubmitModuleResult(False, False, unknown_response)
					return self.result
   				else:
   				 	raise moduleloader.IncorrectModuleReturnType(type(res), type(SubmitModuleResult))
   		# Attempt to handle exceptions if we get one
    		except:
    			if self.debug_output >= moduleloader.DEBUG_ALL:
    				print "Error in execution of %s" % self.module_name
    				print sys.exc_info()[0]
    				
    			if self.fault_tolerance:
   				formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
   				self.result = SubmitModuleResult(False, False, formatted_str)
				return self.result
   			else:
   				raise
			
	# If used complete hander should be of type method(result, user_data)
	def executeThreaded(self, email, message, log_dict, complete_handler = None, user_data = None):
		self.email = email
		self.message = message
		self.log_dict = log_dict
		self.complete_handler = complete_handler
		self.user_data = user_data
		self.start()
		
	def run(self):
		self.result = self.execute(self.email, self.message, self.log_dict)
		if self.complete_handler:
			self.complete_handler(self.result, self.user_data)
			
	def getResult(self):
		return self.result
		
class SubmitValidator(moduleloader.GenericValidator):
	necessary_attributes = moduleloader.GenericValidator.necessary_attributes + ["module_submit_url"]
	necessary_attr_types = moduleloader.GenericValidator.necessary_attr_types + [str]
	ModuleWrapper = SubmitModule
	def __init__(self, parent, plugin_conf, fault_tolerance, debug_output):
		moduleloader.GenericValidator.__init__(self, parent, plugin_conf, fault_tolerance, debug_output)
	
	def validate_additional(self, module):
		valid_hook = self.validate_execution_hook(module, "execute", 3)
		return valid_hook
			
class SubmitModuleLoader(moduleloader.ModuleLoader):
	ValidatorClass = SubmitValidator
	ModuleWrapper = SubmitModule
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output)	
