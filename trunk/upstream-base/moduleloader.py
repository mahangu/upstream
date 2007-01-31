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

# TODO some of the __repr__ seem to try to concatenate strings with non-strings


import glob, sys, os, threading, time, imp, md5, re, imp, Queue

MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_CRITICAL = 1
DEBUG_ALL = 2

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
	def __init__(self, imp_count, imp_lock, package, load_queue, debug_output):
		threading.Thread.__init__(self)
		self.importer_counter = imp_count
		self.importer_lock = imp_lock
		self.package = package
		self.output_queue = load_queue
		self.debug_out = debug_output
		
	def run(self):
		self.importer_lock.acquire()
		self.importer_counter = self.importer_counter + 1
		self.importer_lock.release()
		try:
			imp_pack = __import__(self.package)
			for plugin_name in imp_pack.__all__:
				# This imports the module into imp_pack
				if self.debug_out >= DEBUG_ALL:
					print "Importing %s" % plugin_name
				try:
					__import__(self.package + "." + plugin_name)	
					# Stick in a tuple with the module and the package
					self.output_queue.put((getattr(imp_pack, plugin_name), self.package))	
				except Exception, e:
					if self.debug_out >= DEBUG_CRITICAL:
						print "Exception thrown: %s" % e			
		except Exception, e:
			if self.debug_out >= DEBUG_CRITICAL:
				print "Exception thrown: %s" % e	
		else:
			self.importer_lock.acquire()
			self.importer_counter = self.importer_counter - 1
			self.importer_lock.release()		

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
					
				except ImportError, e:
					if self.debug_output >= DEBUG_CRITICAL:
						print e
				except SyntaxError, e:
					if self.debug_output >= DEBUG_CRITICAL:
						print e
				else:
					# Ensure we close the file if its open
					if file != None:
						file.close()
		except Exception, e:
			if self.debug_out >= DEBUG_CRITICAL:
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
	def __init__(self, validator_run_count, validator_count_lock, importer_count, loader_queue, valid_mods, plugin_config, debug_output):
		threading.Thread.__init__(self)
		self.validator_run_counter = validator_run_count
		self.validator_count_lock = validator_count_lock
		self.importer_count = importer_count
		self.loader_queue = loader_queue
		self.valid_modules = valid_mods
		self.plugin_config = plugin_config
		self.debug_output = debug_output	
		self.fault_tolerance = True
		
	def run(self):
		self.validator_count_lock.acquire()
		self.validator_run_counter = self.validator_run_counter + 1
		self.validator_count_lock.release()
		while self.importer_count > 0 or self.loader_queue.qsize() > 0:
			if self.loader_queue.qsize()> 0:
				try:
					# Get a module and validate it
					m_tuple = self.loader_queue.get()
					module = m_tuple[0]
					package = m_tuple[1]
								
					if self.debug_output >= DEBUG_ALL:
						print "Validating module: %s" % module
					if self.validate_module(module):
						trust_level = self.md5_verify(module, package)
						self.valid_modules.append(self.ModuleWrapper(module, trust_level, self.fault_tolerance, self.debug_output))
				except Exception, e:
					if self.debug_output >= DEBUG_CRITICAL:
						# We lost the import for some reason
						print "Exception thrown: %s" % sys.exc_info()[0]
						print e
			else:
				time.sleep(0.01)
				
		self.validator_count_lock.acquire()
		self.validator_run_counter = self.validator_run_counter - 1 
		self.validator_count_lock.release()
		
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
		if self.debug_output >= DEBUG_ALL:
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
				
		self.importer_running = 0
		self.validator_running = 0
		self.importer_pool = []
		self.validator_pool = []
		self.importer_count_lock = threading.Lock()
		self.validator_count_lock = threading.Lock()		
		
		#These 2 locks are for locking prior to pool modifications
		
		self.load_queue = Queue.Queue()
		self.valid_modules = []
		
		# Initialize the loaders	
		for package_name in self.plugin_config.get_all_packages():
			pack_thread = PackageImporter(self.importer_running, self.importer_count_lock, package_name, self.load_queue, self.debug_output)
			self.importer_pool.append(pack_thread)
			pack_thread.start()
			
		for x in range(0, self.thread_pool_size):
			validate_thread = self.ValidatorClass(self.validator_running, self.validator_count_lock, self.importer_running, self.load_queue, self.valid_modules, self.plugin_config, self.debug_output)
			self.validator_pool.append(validate_thread)			
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
	
	# Deprecated: currently being removed
	def aliveImporter(self):
		for x in self.importer_pool:
			if x.isAlive():
				return True
		return False
	# Deprecated: currently being removed
	def aliveValidator(self):
		for x in self.validator_pool:
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
		for x in self.importer_pool:
			x.join()
		for x in self.validator_pool:
			x.join()
		if self.debug_output >= DEBUG_ALL:
			if self.importer_running > 0:
				print "ERROR: one or more package importers crashed!"
			if self.validator_running > 0:
				print "ERROR: one or more module validators crashed!"
				

class ModuleLoaderIterator:
	def __init__(self, parent):
		self.parent = parent
		self.ind = -1
		
	def next(self):
		self.ind = self.ind + 1
		if self.ind == len(self.parent.valid_modules):
			raise StopIteration
		else:
			return self.parent.valid_modules[self.ind]


