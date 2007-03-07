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
		
	def __str__(self):
		return "Plugin: %s\n%s\nTrust: %s" % (self.__plugin.module_name, self.__plugin.module_description, self.__trust_lvl)

class PluginLoader(threading.Thread):
	__progress_change_ev = threading.Event()
	__find_complete_ev = threading.Event()
	__import_complete_ev = threading.Event()
	__validation_complete_ev = threading.Event()
	__import_queue = Queue.Queue()
	__validation_queue = Queue.Queue()
	__valid_plugins = []
	
	__import_count = 0
	__validation_count = 0	
	__valid_plugin_count = 0
	
	def __init__(self, config, output_sync):
		threading.Thread.__init__(self)
		self.__config = config
		self.__output_sync = output_sync
		
	def run(self):
		self.__find_packages__()
		self.__import_packages__()
		self.__validate_all__()
		
	def wait_progress_change(self):
		self.__progress_change_ev.wait()
		self.__progress_change_ev.clear()
		
	# These events can only happen once, so no need to clear
	def wait_find_complete(self):
		self.__find_complete_ev.wait()
		
	def find_is_complete(self):
		return self.__find_complete_ev.isSet()
		
	def wait_import_complete(self):
		self.__import_complete_ev.wait()
		
	def import_is_complete(self):
		return self.__import_complete_ev.isSet()
		
	def wait_validation_complete(self):
		self.__validation_complete_ev.wait()
		
	def validation_is_complete(self):
		return self.__validation_complete_ev.isSet()
		
	def get_import_count(self):
		return self.__import_count
	
	def get_validation_count(self):
		return self.__validation_count
	
	def get_valid_plugin_count(self):
		return self.__valid_plugin_count
		
	def __new_ostream__(self, title):
		return self.__output_sync.new_stream(title)
	
	def __write_ostream__(self, os_id, msg):
		self.__output_sync.write(os_id, msg)\
		
	def __find_packages__(self):
		pfs_id = self.__new_ostream__("Find Package Log")
		for package in self.__get_config__().get_packages():
			self.__write_ostream__(pfs_id, "Found: %s\n" % package)
			self.__set_found__(package)
			self.__set_progress_changed__()
		self.__find_complete_ev.set()
		
	# Er, who wants to find when one was used and not the other?
	def __set_progress_changed__(self):
		self.__progress_change_ev.set()
		
	def __set_progress_change__(self):
		self.__progress_change_ev.set()
		
	def __import_packages__(self):
		while self.__has_next_to_import__():
			self.__import_one_package__(self.__get_next_to_import__())
		self.__set_import_complete__()
		
	def __import_one_package__(self, package):
		pis_id = self.__new_ostream__("Package Import Log: %s" % package)
		try:
			# Import the package here
			package_obj = __import__(package)
			self.__write_ostream__(pis_id, "Package %s loaded successfully\n" % package)
			for module in package_obj.__all__:
				try:
					# Most of the actual functional code is in this tiny little block
					__import__("%s.%s" % (package, module))
					module_obj = getattr(package_obj, module)
					self.__write_ostream__(pis_id, "Module %s imported successfully\n" % module_obj)
					module_obj.package = package
					self.__set_imported__(module_obj)
					# Set as imported
					self.__import_count = self.__import_count + 1
					self.__set_progress_change__()
				except ImportError, e:
					self.__write_ostream__(pis_id, "Module %s could not be imported due to Import Error\n\t%s\n" % (module, e))
				except SyntaxError, e:
					self.__write_ostream__(pis_id, "Module %s could not be imported due to Syntax Error\n\t%s\n" % (module, e))
				except Exception, e:
					self.__write_ostream__(pis_id, "Module %s could not be imported due to Exception\n\t%s\n" % (module, e))
		except ImportError, e:
			self.__write_ostream__(pis_id, "Package %s could not be loaded due to Import Error\n\t%s\n" % (package, e))
		except SyntaxError, e:
			self.__write_ostream__(pis_id, "Package %s could not be loaded due to Syntax Error\n\t%s\n" % (package, e))
		except Exception, e:
			self.__write_ostream__(pis_id, "Package %s could not be loaded due to Exception\n\t%s\n" % (package, e))
		
	def __set_import_complete__(self):
		self.__import_complete_ev.set()
		self.__set_progress_changed__()
		
	def __validate_all__(self):		
		while self.__has_next_to_validate__():
			plugin = self.__get_next_to_validate__()
			pvl_id = self.__new_ostream__("Validation Log: %s" % plugin.__name__)
			if self.__valid_plugin__(plugin, pvl_id):
				self.__set_validated__(plugin, pvl_id)
			self.__validation_count = self.__validation_count + 1
			self.__set_progress_change__()
		self.__set_validation_complete__()
		self.__set_progress_change__()
		
	
	def __valid_plugin__(self, plugin, pvl_id):
		try:
			if self.__validate_fields__(plugin, REQUIRED_FIELDS, True, pvl_id):
				return True
		except Exception, e:
			self.__write_ostream__(pvl_id, "Validation failed with Exception:\n\t%s" % e)
		return False
	
	def __validate_fields__(self, plugin, fields, full_scan, pvl_id):
		valid = True
		for property in fields:
				self.__write_ostream__(pvl_id, "Has field %s: %s\n" % (property[0], hasattr(plugin, property[0])))
				if not hasattr(plugin, property[0]):					
					valid = False
				else:
					self.__write_ostream__(pvl_id, "Field %s is of type %s\n" % (property[1], isinstance(getattr(plugin, property[0]), property[1])))
					if not isinstance(getattr(plugin, property[0]), property[1]):
						valid = False
				# Return immediately if we don't want a full scan
				if not full_scan and not valid:
					return Valid
		return valid
	
	def __md5_verify__(self, module, log_id):
		md5er = md5.new()		
		fp = open(module.__file__)
		d = fp.read(1024)
		while d:
			md5er.update(d)
			d = fp.read(1024)
		fp.close()
		m_hex = md5er.hexdigest()
		name = self.__construct_fname(module)
		md5sum = self.__config.get_plugin_md5(module.package, name)
		self.__write_ostream__(log_id, "%s\n\tmd5 expected %s\n\tmd5 real %s\n" % (module.__name__, md5sum, m_hex))
		if md5sum == m_hex:
			return TRUSTED
		elif md5sum == None:
			return UNKNOWN
		else:
			return UNTRUSTED
		
	def __construct_fname(self, module):
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
	
	def __set_validation_complete__(self):
		self.__validation_complete_ev.set()
		self.__set_progress_changed__()
		
	def __set_found__(self, package):
		self.__import_queue.put(package)
			
	def __has_next_to_import__(self):
		return not self.__import_queue.empty()
	
	def __get_next_to_import__(self):
		return self.__import_queue.get_nowait()
		
	def __set_imported__(self, plugin):
		self.__validation_queue.put(plugin)
		
	def __has_next_to_validate__(self):
		return not self.__validation_queue.empty()
	
	def __get_next_to_validate__(self):
		return self.__validation_queue.get_nowait()
	
	def __set_validated__(self, plugin, pvl_id):
		plugin_obj = Plugin(plugin, self.__md5_verify__(plugin, pvl_id))
		self.__valid_plugin_count = self.__valid_plugin_count + 1
		self.__valid_plugins.append(plugin_obj)
		
	def __get_config__(self):
		return self.__config
	
	def __str__(self):
		return "Module Loader:\n" + repr(self.valid_modules)
	
	def __getitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError, "Index was not an int or str"
		# Find at index
		if type(modid) is int:
			if modid >= len(self.valid_modules) or modid < 0:
				raise IndexError
			else:
				return self.valid_modules[modid]
		# Find at id
		if type(modid) is str:		
			for mod in self.valid_modules:
				if mod.module_name == modid:
					return mod
			raise KeyError
		
	def __delitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError, "Index was not an int or str"
		# Find at index
		if type(modid) is int:
			if modid >= len(self.valid_modules) or modid < 0:
				raise IndexError
			else:
				self.valid_modules.remove(self.valid_modules[modid])
		# Find at id
		if type(modid) is str:		
			# This will already raise an exception if necessary
			mod = self.__getitem__(modid)
			self.valid_modules.remove(mod)
					
	def __len__(self):
		return len(self.__valid_plugins)
			
	def __iter__(self):
		return ModuleLoaderIterator(self)
	
	def __get_plugins__(self):
		return self.__valid_plugins
	
class ModuleLoaderIterator:
	def __init__(self, parent):
		self.parent = parent
		self.ind = -1
		
	def next(self):
		self.ind = self.ind + 1
		if self.ind == len(self.parent.__get_plugins__()):
			raise StopIteration
		else:
			return self.parent.__get_plugins__()[self.ind]

	# Provide a string method
	
	
MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_ALL = 1

HASH_TRUSTED = 0
HASH_UNTRUSTED = 1
HASH_DANGEROUS = 2

# Perhaps this will change later
THREAD_POOL_MAX = 3

# LoadedModule now extends from Thread type
class LoadedModule(threading.Thread):
	fault_tolerance = True
	debug_output = DEBUG_NONE
	# This expects the module fields to already exist
	# Note: any new module wrappers must have this exact argument list
	def __init__(self, module, trust_level, fault_tolerance, debug_output):
		threading.Thread.__init__(self)
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		self.module = module
		self.trust_level = trust_level
		self.module_name = self.module.module_name
		self.module_description = self.module.module_description
	def __repr__(self):
		return "<loaded module : %s with trust %d>" % (self.module, self.trust_level)		

class PackageImporter(threading.Thread):
	def __init__(self, parent, package, debug_output=False):
		threading.Thread.__init__(self)
		self.parent = parent
		self.package = package
		self.debug_output = debug_output
		
	def run(self):
		try:
			imp_pack = __import__(self.package)
			for plugin_name in imp_pack.__all__:
				# This imports the module into imp_pack
				if self.debug_output >= DEBUG_ALL:
					print "Importing %s" % plugin_name
				try:
					__import__(self.package + "." + plugin_name)	
					# Stick in a tuple with the module and the package
					self.parent.load_queue.append((getattr(imp_pack, plugin_name), self.package))				
					self.parent.found_lock.acquire()
					self.parent.total_found_mod = self.parent.total_found_mod + 1
					self.parent.found_lock.release()				
				except Exception, e:
					print "Exception thrown: %s" % sys.exc_info()[0]					
					print e			
		except Exception, e:
			# We lost the whole package for some reason
			print "Exception thrown: %s" % sys.exc_info()[0]
			print e
		else:
			# When done, mark ourselves as successfully finished
			self.parent.valid_lock.acquire()
			self.parent.pack_running = self.parent.pack_running - 1
			self.parent.valid_lock.release()		

class ExtraImporter(threading.Thread):
	def __init__(self, parent, imp_list):
		threading.Thread.__init__(self)
		self.parent = parent
		self.import_list = imp_list
		
	def run(self):
		try:
			for m_descr in self.import_list:	
				# Get a full path
				last_p_sep = m_descr.rfind("/")
				if last_p_sep >= 0:
					file_str = m_descr[last_p_sep + 1:]
					path_str = m_descr[0:last_p_sep]
				else:
					file_str = m_descr
					path_str = "./"
				
				# Remove .py or anything else from filename
				loc_split = file_str.rfind(".py")
				if loc_split >= 0:
					module_str = file_str[0:loc_split]
				else:
					module_str = file_str
				try:
					file = None
					
					file, pathname, descr = imp.find_module(module_str, [path])
					module = imp.load_module("additional_" + module_str, file, file.name, descr)
					
					self.parent.load_queue.append((getattr(imp_pack, plugin_name), self.package))				
					self.parent.found_lock.acquire()
					self.parent.total_found_mod = self.parent.total_found_mod + 1
					self.parent.found_lock.release()	
					
				except ImportError, e:
					if self.debug_output:
						print e
					return False
				except SyntaxError, e:
					if self.debug_output:
						print e
				else:
					# Ensure we close the file if its open
					if file != None:
						file.close()
		except Exception, e:
			if self.debug_out >= DEBUG_ALL:
				print e
				
		else:
			# When done, mark ourselves as successfully finished
			self.parent.valid_lock.acquire()
			self.parent.pack_running = self.parent.pack_running - 1
			self.parent.valid_lock.release()	

# This is a worker class for validating modules. It idles and waits for a module
class GenericValidator(threading.Thread):
	necessary_attributes = ["module_name", "module_description"]
	necessary_attr_types = [str, str]
	ModuleWrapper = LoadedModule
	
	def __init__(self, parent, plugin_config, fault_tolerance, debug_output):
		threading.Thread.__init__(self)
		self.parent = parent
		self.plugin_config = plugin_config
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance		
		
	def run(self):
		while self.parent.aliveImporter() or len(self.parent.load_queue) > 0:
			if len(self.parent.load_queue) > 0:
				try:
					# Get a module and validate it
					m_tuple = self.parent.load_queue.pop(0)
					module = m_tuple[0]
					package = m_tuple[1]
								
					if self.debug_output >= 1:
						print "Validating module: %s" % module
					if self.validate_module(module):
						trust_level = self.md5_verify(module, package)
						self.parent.valid_modules.append(self.ModuleWrapper(module, trust_level, self.fault_tolerance, self.debug_output))					
						self.parent.loaded_lock.acquire()
						# Not really loaded, but processed
						self.parent.total_loaded_mod = self.parent.total_loaded_mod + 1
						self.parent.loaded_lock.release()
				except Exception, e:
					# We lost the import for some reason
					print "Exception thrown: %s" % sys.exc_info()[0]
					print e
			else:
				time.sleep(0.01)
				
		self.parent.valid_lock.acquire()
		self.parent.valid_running = self.parent.valid_running - 1
		self.parent.valid_lock.release()				
		
	def md5_verify(self, module, package):
		md5er = md5.new()
		
		fp = open(module.__file__)				
		d = fp.read(1024)
		while d:
			md5er.update(d)
			d = fp.read(1024)
		fp.close()
		
		m_hex = md5er.hexdigest()
		
		end_str = ""
		if module.__file__.rfind(".pyc") != -1:
			end_str = "pyc"
		elif module.__file__.rfind(".py") != -1:
			end_str = "py"		
		else:
			end_str = "pyo"
		
		# We may have imported from a package, so get rid of the .
		regex = re.compile("\.")
		name_split = regex.split(module.__name__)
		name = name_split[len(name_split) - 1]
		md5sum = self.plugin_config.get_md5(package, name, end_str)
		if self.debug_output >= 1:
			print "%s md5 expected %s" % (module.__name__, md5sum)
			print "%s md5 real %s" % (module.__name__, m_hex)
		if md5sum == m_hex:
			return HASH_TRUSTED
		elif md5sum == None:
			return HASH_UNTRUSTED
		else:
			return HASH_DANGEROUS
			
		
	# This is the bare minimum necessary for one of our		
	def validate_module(self, module):
		if self.debug_output >= DEBUG_ALL:
			print "Validating module: %s" % module.__name__
		return self.validate_fields(module) and self.validate_additional(module)
		
	# Determine if the module has the necessary fields to be a valid module
	# Subclasses should probably not have to override this method, and
	# instead, they should rely on overriding the "necessary_attributes" field
	def validate_fields(self, module):
		for field in self.necessary_attributes:
			if self.debug_output >= DEBUG_ALL:
				print " Validating fields %s : %s" % (field, hasattr(module, field))
			if not hasattr(module, field):
				return False
			ind = self.necessary_attributes.index(field)
			# This only runs when we have actually specified out to that
			# type
			if ind < self.necessary_attr_types:
				# Ahh ye olde debugging output, you take up so much space
				if self.debug_output >= DEBUG_ALL:
					print " Validating field %s as type %s : %s" % (field, self.necessary_attr_types[ind], isinstance(module.__dict__[field], self.necessary_attr_types[ind]) and self.necessary_attr_types[ind] is not None)
				
				if not isinstance(module.__dict__[field], self.necessary_attr_types[ind]) and self.necessary_attr_types[ind] is not None:
					return False
		# If we get to the end, we were successful
		return True
	
	def validate_additional(self, module):
		return True
		
	# This is not actually used by default, but is provided as a convenience,
	# so that base classes do not have to reimplement it
	def validate_execution_hook(self, module, name, num_args):
		if self.debug_output >= DEBUG_ALL:
			print " Module %s has attribute %s: %s " % (module, name, hasattr(module, name))
			print " Module attribute %s is of type 'func_code': %s" % (name, hasattr(module.__dict__[name], "func_code"))
			print " Module function %s has %d args: %s" % (name, num_args, module.__dict__[name].func_code.co_argcount is num_args)
		return hasattr(module, name) and hasattr(module.__dict__[name], "func_code") and module.__dict__[name].func_code.co_argcount is num_args

# ModuleLoader is largely a container that provides methods
class ModuleLoader:	
	# New classes should override the ModuleWrapper item
	ValidatorClass = GenericValidator
	ModuleWrapper = LoadedModule
	def __init__(self, plugin_config, fault_tolerance, debug_output=DEBUG_NONE, thread_pool_size = THREAD_POOL_MAX):
		# Chain up
		self.plugin_config = plugin_config
				
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance
		self.thread_pool_size = thread_pool_size
		# Intense weirdness seems to happen if this is static initialized
		self.pack_running = 0
		self.valid_running = 0
		self.pack_pool = []
		self.valid_pool = []
		#These 2 locks are for locking prior to pool modifications
		self.pack_lock = threading.Lock()
		self.valid_lock = threading.Lock()
		
		self.load_queue = []
		self.valid_modules = []
		self.found_lock = threading.Lock()
		self.loaded_lock = threading.Lock()
		self.total_found_mod = 0
		self.total_loaded_mod = 0
		
		# Initialize the loaders	
		for pack in self.plugin_config.get_all_packages():
			pack_thread = PackageImporter(self, pack, self.debug_output)
			
			self.pack_lock.acquire()
			self.pack_running = self.pack_running + 1
			self.pack_pool.append(pack_thread)
			self.pack_lock.release()
			
			pack_thread.start()
			
		for x in range(0, self.thread_pool_size):
			validate_thread = self.ValidatorClass(self, self.plugin_config, self.fault_tolerance, self.debug_output)
			
			self.valid_lock.acquire()
			self.valid_running = self.valid_running + 1
			self.valid_pool.append(validate_thread)
			self.valid_lock.release()
			
			validate_thread.start()			
	
	def __repr__(self):
		return "ModuleValidator(" + repr(self.parent) + ")"
	
	def __getitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError
		# Find at index
		if type(modid) is int:
			if modid >= len(self.valid_modules) or modid < 0:
				raise IndexError
			else:
				return self.valid_modules[modid]
		# Find at id
		if type(modid) is str:		
			for mod in self.valid_modules:
				if mod.module_name == modid:
					return mod
			raise KeyError
		
	def __delitem__(self, modid):
		if type(modid) is not str and type(modid) is not int:
			raise TypeError
		# Find at index
		if type(modid) is int:
			if modid >= len(self.valid_modules) or modid < 0:
				raise IndexError
			else:
				self.valid_modules.remove(self.valid_modules[modid])
		# Find at id
		if type(modid) is str:		
			# This will already raise an exception if necessary
			mod = self.__getitem__(modid)
			self.valid_modules.remove(mod)			
					
	def __len__(self):
		return len(self.valid_modules)
			
	def __iter__(self):
		return ModuleLoaderIterator(self)
	# Provide a string method
	def __str__(self):
		return "Module Loader:\n" + repr(self.valid_modules)
	
	def aliveImporter(self):
		for x in self.pack_pool:
			if x.isAlive():
				return True
		return False
		
	def aliveValidator(self):
		for x in self.valid_pool:
			if x.isAlive():
				return True
		return False
	
	def getValidCompleteRatio(self):
		if self.total_found_mod:
			return (self.total_loaded_mod + 0.0)/self.total_found_mod
		else:
			return 0
	
	def loadAdditionalModule(self, full_path):
		self.loadAdditionalModules([full_path])
		
	def loadAdditionalModules(self, full_path_list):
		if isinstance(full_path_list, list):
			ex_thread = ExtraImporter(self, full_path_list)
			self.pack_lock.acquire()
			self.pack_running = self.pack_running + 1
			self.pack_pool.append(ex_thread)
			self.pack_lock.release()
			ex_thread.start()
			
			if len(full_path_list) > self.thread_pool_size:
				for x in range(0, self.thread_pool_size):
					validate_thread = self.ValidatorClass(self, self.plugin_config, self.fault_tolerance, self.debug_output)
				
					self.valid_lock.acquire()
					self.valid_running = self.valid_running + 1
					self.valid_pool.append(validate_thread)
					self.valid_lock.release()
					
					validate_thread.start()		
			else:
				validate_thread = self.ValidatorClass(self, self.plugin_config, self.fault_tolerance, self.debug_output)
			
			self.valid_lock.acquire()
			self.valid_running = self.valid_running + 1
			self.valid_pool.append(validate_thread)
			self.valid_lock.release()
			
			validate_thread.start()	
			return True
		else:
			return False		
		
		
		
	# This is a faux join method that will wait until all of the thread pools 
	# have completed their work
	def join(self):
		for x in self.pack_pool:
			x.join()
		for x in self.valid_pool:
			x.join()
		if self.debug_output >= DEBUG_ALL:
			if self.pack_running > 0:
				print "ERROR: one or more package importers crashed!"
			if self.pack_running > 0:
				print "ERROR: one or more module validators crashed!"
				



