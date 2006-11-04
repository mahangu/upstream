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

import glob, imp, sys, os, threading, time

#  This module was built with the goal of maximum fault tolerance for
#  any imported modules.  If there is a discovered case in which
#  fault tolerance

MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_ALL = 1

# Perhaps this will change later
THREAD_POOL_MAX = 5

class ModuleLoaderInitException(Exception):
	def __init__(self, err_type):
		Exception.__init__(self)
		self.err_type = err_type
	def __repr__(self):
		return "raised ModuleLoaderInitException(" + self.err_type + ")"
	def __str__(self):
		if self.err_type == MLOAD_NOT_LIST:
			return "Error: Package list was not a list"
		elif self.err_type == MLOAD_EMPTY_LIST:
			return "Error: Package list was empty"
		elif self.err_type == MLOAD_HAS_NONSTR:
			return "Error: Package list contained non-strings"
		else:
			return "Error: unknown?"
			
			
class IncorrectModuleReturnType(Exception):
	def __init__(self, found_type, expected_type):
		Exception.__init__(self)
		self.found_type = found_type
		self.expected_type = expected_type
	def __repr__(self):
		return "raised IncorrectModuleReturnType(" + self.found_type + "," + self.expected_type + ")"
	def __str__(self):
		return "Found type: " + self.found_type + " Expected type: " + self.expected_type

# LoadedModule now extends from Thread type
class LoadedModule(threading.Thread):
	fault_tolerance = True
	debug_output = DEBUG_NONE
	# This expects the module fields to already exist
	# Note: any new module wrappers must have this exact argument list
	def __init__(self, module, fault_tolerance, debug_output):
		threading.Thread.__init__(self)
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		self.module = module
		self.module_name = self.module.module_name
		self.module_description = self.module.module_description
	def __repr__(self):
		return "< loaded module with name : %s >" % self.module_name
		

class PackageImporter(threading.Thread):
	def __init__(self, parent, package, fault_tolerance, debug_output=False):
		threading.Thread.__init__(self)
		self.parent = parent
		self.package = package
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		
	def run(self):
		if self.debug_output >= DEBUG_ALL:
			print "Beginning threaded ModuleImporter on package %s" % self.package
		imp_pack = __import__(self.package)
		for plugin_name in imp_pack.__all__:
			# This imports the module into imp_pack
			if self.debug_output >= DEBUG_ALL:
				print "Importing: %s" % self.package + "." + plugin_name
			try:
				__import__(self.package + "." + plugin_name)
			except:
				print "Exception thrown: %s" % sys.exc_info()[0]
				if not self.fault_tolerance:
					raise
			self.parent.load_queue.append(getattr(imp_pack, plugin_name))
			
			self.parent.found_lock.acquire()
			self.parent.total_found_mod = self.parent.total_found_mod + 1
			self.parent.found_lock.release()
			
		# When done pop ourselves off the stack
		
		self.parent.package_importer_pool.remove(self)
		if self.debug_output >= DEBUG_ALL:
			print "Ending threading importer on package %s" % self.package
			print "Import pool: %s" % self.parent.package_importer_pool
			
# This is a worker class for validating modules. It idles and waits for a module
class GenericValidator(threading.Thread):
	necessary_attributes = ["module_name", "module_description"]
	necessary_attr_types = [str, str]
	ModuleWrapper = LoadedModule
	
	def __init__(self, parent, fault_tolerance, debug_output):
		threading.Thread.__init__(self)
		self.parent = parent
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance
		
	def run(self):
		if self.debug_output >= DEBUG_ALL:
			print "Beginning threaded Validator"
		while len(self.parent.package_importer_pool) > 0 or len(self.parent.load_queue) > 0:
			if self.debug_output >= DEBUG_ALL:
				print "Package importer pool size: %d" % len(self.parent.package_importer_pool)
				
			if len(self.parent.load_queue) > 0:
				
				# Get a module and validate it
				module = self.parent.load_queue.pop(0)
				if self.debug_output >= 1:
					print "Validating module: %s" % module
				if self.validate_module(module):
					self.parent.valid_modules.append(self.ModuleWrapper(module, self.fault_tolerance, self.debug_output))
					
					self.parent.loaded_lock.acquire()
					self.parent.total_loaded_mod = self.parent.total_loaded_mod + 1
					self.parent.loaded_lock.release()
			else:
				time.sleep(0.01)
		
		self.parent.module_validator_pool.remove(self)
		if self.debug_output >= DEBUG_ALL:
			print "Validator pool: %s" % self.parent.module_validator_pool
			print "Ending threaded validator"
								
	# This is the bare minimum necessary for one of our		
	def validate_module(self, module):
		if self.debug_output >= DEBUG_ALL:
			print "Validating module: %s" % module.__name__
		valid_fields = self.validate_fields(module) 
		valid_additional = self.validate_additional(module)
		return valid_fields and valid_additional
		
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
					print " Validating field %s as type %s : %s" % (field, self.necessary_attr_types[ind], type(module.__dict__[field]) == self.necessary_attr_types[ind] and self.necessary_attr_types[ind] is not None)
				
				if not type(module.__dict__[field]) == self.necessary_attr_types[ind] and self.necessary_attr_types[ind] is not None:
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
		
	load_queue = []
	valid_modules = []
	
	found_lock = threading.Lock()
	loaded_lock = threading.Lock()
	total_found_mod = 0
	total_loaded_mod = 0
	
	package_importer_pool = []
	module_validator_pool = []
	
	# New classes should override the ModuleWrapper item
	ValidatorClass = GenericValidator
	ModuleWrapper = LoadedModule
	def __init__(self, pack_list, fault_tolerance, debug_output=DEBUG_NONE):
		# Chain up
		self.pack_list = pack_list
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance
		# Initialize the loaders	
		for pack in self.pack_list:
			pack_thread = PackageImporter(self, pack, self.fault_tolerance, self.debug_output)
			self.package_importer_pool.append(pack_thread)
			pack_thread.start()
			
		for x in range(0, THREAD_POOL_MAX):
			validate_thread = self.ValidatorClass(self, self.fault_tolerance, self.debug_output)
			self.module_validator_pool.append(validate_thread)
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
		return "Module loader:\n" + repr(self.valid_modules)
	
	# This is a faux join method that will wait until all of the thread pools 
	# have completed their work
	def join(self):
		while len(self.package_importer_pool) and len(self.module_validator_pool) > 0:
			time.sleep(0.01)
			if self.debug_output >= 1:
				print "Idling in join"

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


