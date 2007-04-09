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

# TODO figure out which modules we don't actually need to import so startup is
# increased


import glob, sys, os, threading, time, imp, md5, re, imp, Queue, logsynchronizer

MAX_THREADS = 3

UNTRUSTED = -1
UNKNOWN = 0
TRUSTED = 1

# These are required things

REQUIRED_FIELDS = [("module_name", str), ("module_description", str)]

class Plugin:
	def __init__(self, plugin, trust_lvl):
		self.__plugin = plugin
		self.__trust_lvl = trust_lvl
		
		self.module_name = self.__plugin.module_name
		self.module_description = self.__plugin.module_description
		
	def getPlugin(self):
		return self.__plugin
		
	def __repr__(self):
		return self.__str__()
	
	def __str__(self):
		return "Plugin: %s with trust: %s" % (self.__plugin.module_name, self.__trust_lvl)

class PluginLoader(threading.Thread):	
	def __init__(self, config, output_sync):
		threading.Thread.__init__(self)
		# Not sure why these can't be stuff
		self.__progress_change_ev = threading.Event()
		self.__find_complete_ev = threading.Event()
		self.__import_complete_ev = threading.Event()
		self.__validation_complete_ev = threading.Event()
		self.__import_queue = Queue.Queue()
		self.__validation_queue = Queue.Queue()
		self.__valid_plugins = []
		self.__import_count = 0
		self.__validation_count = 0	
		self.__valid_plugin_count = 0
		self.__config = config
		self.__output_sync = output_sync
		
	def run(self):
		self.__findPackages__()
		self.__importPackages__()
		self.__validateAll__()
		
	def waitProgressChange(self, timeout = 0):
		self.__progress_change_ev.wait(timeout)
		self.__progress_change_ev.clear()
		
	# These events can only happen once, so no need to clear
	def waitFindComplete(self, timeout = 0):
		self.__find_complete_ev.wait(timeout)
		
	def findIsComplete(self):
		return self.__find_complete_ev.isSet()
		
	def waitImportComplete(self, timeout = 0):
		self.__import_complete_ev.wait(timeout)
		
	def importIsComplete(self):
		return self.__import_complete_ev.isSet()
		
	def waitValidationComplete(self, timeout = 0):
		self.__validation_complete_ev.wait(timeout)
		
	def validationIsComplete(self):
		return self.__validation_complete_ev.isSet()
	
	def getCompleteFrac(self):
		if self.__import_count == 0:
			return -1
		else:
			return (self.__validation_count + 0.0)/self.__import_count
		
	def getImportCount(self):
		return self.__import_count
	
	def getValidationCount(self):
		return self.__validation_count
	
	def getValidPluginCount(self):
		return self.__valid_plugin_count
	
	def getValidPlugins(self):
		return self.__valid_plugins
		
	def __newOstream__(self, title):
		return self.__output_sync.new_stream(title)
	
	def __writeOstream__(self, os_id, msg):
		self.__output_sync.write(os_id, msg)\
		
	def __findPackages__(self):
		pfs_id = self.__newOstream__("Find Package Log")
		for package in self.__getConfig__().getPackages():
			self.__writeOstream__(pfs_id, "Found: %s\n" % package)
			self.__setFound__(package)
		self.__find_complete_ev.set()
		
	# Er, who wants to find when one was used and not the other?
	def __setProgressChanged__(self):
		self.__progress_change_ev.set()
		
	def __set_progress_change__(self):
		self.__progress_change_ev.set()
		
	def __importPackages__(self):
		while self.__hasNextToImport__():
			self.__import_one_package__(self.__getNextToImport__())
		self.__set_import_complete__()
		
	def __import_one_package__(self, package):
		pis_id = self.__newOstream__("Package Import Log: %s" % package)
		try:
			# Import the package here
			package_obj = __import__(package)
			self.__writeOstream__(pis_id, "Package %s loaded successfully\n" % package)
			for module in package_obj.__all__:
				try:
					# Most of the actual functional code is in this tiny little block
					__import__("%s.%s" % (package, module))
					module_obj = getattr(package_obj, module)
					self.__writeOstream__(pis_id, "Module %s imported successfully\n" % module_obj)
					module_obj.package = package
					self.__setImported__(module_obj)
					# Set as imported
					self.__import_count = self.__import_count + 1
					self.__set_progress_change__()
				except ImportError, e:
					self.__writeOstream__(pis_id, "Module %s could not be imported due to Import Error\n\t%s\n" % (module, e))
				except SyntaxError, e:
					self.__writeOstream__(pis_id, "Module %s could not be imported due to Syntax Error\n\t%s\n" % (module, e))
				except Exception, e:
					self.__writeOstream__(pis_id, "Module %s could not be imported due to Exception\n\t%s\n" % (module, e))
		except ImportError, e:
			self.__writeOstream__(pis_id, "Package %s could not be loaded due to Import Error\n\t%s\n" % (package, e))
		except SyntaxError, e:
			self.__writeOstream__(pis_id, "Package %s could not be loaded due to Syntax Error\n\t%s\n" % (package, e))
		except Exception, e:
			self.__writeOstream__(pis_id, "Package %s could not be loaded due to Exception\n\t%s\n" % (package, e))
		
	def __set_import_complete__(self):
		self.__import_complete_ev.set()
		self.__setProgressChanged__()
		
	def __validateAll__(self):		
		while self.__hasNextToValidate__():
			plugin = self.__getNextToValidate__()
			pvl_id = self.__newOstream__("Validation Log: %s" % plugin.__name__)
			if self.__valid_plugin__(plugin, pvl_id):
				self.__isValidated__(plugin, pvl_id)
			self.__validation_count = self.__validation_count + 1
			self.__set_progress_change__()
		self.__setValidationComplete__()
		self.__set_progress_change__()
		
	
	def __valid_plugin__(self, plugin, pvl_id):
		try:
			if self.__validate_fields__(plugin, REQUIRED_FIELDS, True, pvl_id):
				return True
		except Exception, e:
			self.__writeOstream__(pvl_id, "Validation failed with Exception:\n\t%s" % e)
		return False
	
	def __validate_fields__(self, plugin, fields, full_scan, pvl_id):
		valid = True
		for property in fields:
				self.__writeOstream__(pvl_id, "Has field %s: %s\n" % (property[0], hasattr(plugin, property[0])))
				if not hasattr(plugin, property[0]):					
					valid = False
				else:
					self.__writeOstream__(pvl_id, "Field %s is of type %s: %s\n" % (property[0], property[1], isinstance(getattr(plugin, property[0]), property[1])))
					# This also ignores Nonetypes
					if not isinstance(getattr(plugin, property[0]), property[1]) and property[1] != None:
						valid = False
				# Return immediately if we don't want a full scan
				if not full_scan and not valid:
					return valid
		return valid
	
	def __validate_function__(self, plugin, func_name, param, pvl_id):
			has_attr =  hasattr(plugin, func_name)
			if has_attr:
				is_func_code = hasattr(plugin.__dict__[func_name], "func_code")
			else:
				is_func_code = False
			if has_attr and is_func_code:
				has_args = plugin.__dict__[func_name].func_code.co_argcount == param
			else:
				has_args = 0
				
			self.__writeOstream__(pvl_id, "Module %s has attribute %s: %s\n" % (plugin, func_name, has_attr))
			self.__writeOstream__(pvl_id, "Module attribute %s is of type 'func_code': %s\n" % (func_name, is_func_code))
			self.__writeOstream__(pvl_id, "Module function %s has %d args: %s\n" % (func_name, param, has_args))
			return has_attr and is_func_code and has_args
		
	
	def __md5Verify__(self, module, log_id):
		md5er = md5.new()		
		fp = open(module.__file__)
		d = fp.read(1024)
		while d:
			md5er.update(d)
			d = fp.read(1024)
		fp.close()
		m_hex = md5er.hexdigest()
		name = self.__constructFileName__(module)
		md5sum = self.__config.getPluginMD5(module.package, name)
		self.__writeOstream__(log_id, "%s\n\tmd5 expected %s\n\tmd5 real %s\n" % (module.__name__, md5sum, m_hex))
		if md5sum == m_hex:
			return TRUSTED
		elif md5sum == None:
			return UNKNOWN
		else:
			return UNTRUSTED
		
	def __constructFileName__(self, module):
		regex = re.compile("\.")
		name_split = regex.split(module.__name__)
		name = name_split[len(name_split) - 1]
		if module.__file__.rfind(".pyc") != -1:
			end_str = "pyc"
		elif module.__file__.rfind(".py") != -1:
			end_str = "py"		
		else:
			end_str = "pyo"
		return name + '_' + end_str
	
	def __setValidationComplete__(self):
		self.__validation_complete_ev.set()
		self.__setProgressChanged__()
		
	def __setFound__(self, package):
		self.__import_queue.put(package)
		self.__setProgressChanged__()

			
	def __hasNextToImport__(self):
		return not self.__import_queue.empty()
	
	def __getNextToImport__(self):
		return self.__import_queue.get()
		
	def __setImported__(self, plugin):
		self.__validation_queue.put(plugin)
		
	def __hasNextToValidate__(self):
		return not self.__validation_queue.empty()
	
	def __getNextToValidate__(self):
		return self.__validation_queue.get()
	
	def __isValidated__(self, plugin, pvl_id):
		plugin_obj = Plugin(plugin, self.__md5Verify__(plugin, pvl_id))
		self.__addValidPlugin__(plugin_obj)		
		
	def __addValidPlugin__(self, plugin_obj):
		self.__valid_plugin_count = self.__valid_plugin_count + 1
		self.__valid_plugins.append(plugin_obj)
		self.__set_progress_change__()
		
	def __getConfig__(self):
		return self.__config
	
	def __str__(self):
		return "Module Loader:\n" + repr(self.__valid_plugins)
	
	def __getitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError, "Index was not an int or str"
		# Find at index
		if type(modid) is int:
			if modid >= len(self.__valid_plugins) or modid < 0:
				raise IndexError
			else:
				return self.__valid_plugins[modid]
		# Find at id
		if type(modid) is str:		
			for mod in self.__valid_plugins:
				if mod.module_name == modid:
					return mod
			raise KeyError
		
	def __delitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError, "Index was not an int or str"
		# Find at index
		if type(modid) is int:
			if modid >= len(self.__valid_plugins) or modid < 0:
				raise IndexError
			else:
				self.__valid_plugins.remove(self.valid_modules[modid])
		# Find at id
		if type(modid) is str:		
			# This will already raise an exception if necessary
			mod = self.__getitem__(modid)
			self.__valid_plugins.remove(mod)
					
	def __len__(self):
		return len(self.__valid_plugins)
			
	def __iter__(self):
		return self.__valid_plugins.__iter__()
	
	def __getPlugins__(self):
		return self.__valid_plugins

# vim:set noexpandtab: 
