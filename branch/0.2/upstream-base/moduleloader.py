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


import glob, sys, os, threading, time, imp, md5, re



MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_ALL = 1

HASH_TRUSTED = 0
HASH_UNTRUSTED = 1
HASH_DANGEROUS = 2

# Perhaps this will change later
THREAD_POOL_MAX = 5

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
				
				
			# When done, mark ourselves as successfully finished
			self.parent.valid_lock.acquire()
			self.parent.pack_running = self.parent.pack_running - 1
			self.parent.valid_lock.release()
		except Exception, e:
			# We lost the whole package for some reason
			print "Exception thrown: %s" % sys.exc_info()[0]
			print e				

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
		while self.parent.pack_running > 0 or len(self.parent.load_queue) > 0:
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
	
	def getValidCompleteRatio(self):
		if self.total_found_mod:
			return (self.total_loaded_mod + 0.0)/self.total_found_mod
		else:
			return 0
	
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


