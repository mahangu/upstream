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

# This module provides support for our module import facilities
# there seems to exist a more "pythony" way of doing this via
# import hooks.  This is an area of future development, i.e. determine
# if it is viable for what we want to do.  Currently we use unbound
# import hooks which means we never have to deal with complex implementation
# details


# TODO some of the __repr__ seem to try to concatenate strings with non-strings

import glob, imp, sys

#  This module was built with the goal of maximum fault tolerance for
#  any imported modules.  If there is a discovered case in which
#  fault tolerance

MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_ALL = 1

class ModuleLoaderInitException(Exception):
	def __init__(self, err_type):
		Exception.__init__(self)
		self.err_type = err_type
	def __repr__(self):
		return "raised ModuleLoaderInitException(" + self.err_type + ")"
	def __str__(self):
		if self.err_type == MLOAD_NOT_LIST:
			return "Error: Module path list was not a list"
		elif self.err_type == MLOAD_EMPTY_LIST:
			return "Error: Module path list was empty"
		elif self.err_type == MLOAD_HAS_NONSTR:
			return "Error: Module path list contained non-string paths"
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
		
# Raised when a module was unloadable for some reason
class ModuleUnloadeableException(Exception):
	def __init__(self, module_name, reason):
		Exception.__init__(self)
		self.reason = reason
		self.module_name = module_name
	def __repr__(self):
		return "rasied ModuleUnloadeableException(" + self.reason + ")"
	def __str__(self):
		return "Module %s unloadeable: %s" % ( self.module_name, self.reason)

class LoadedModule:
	fault_tolerance = True
	debug_output = DEBUG_NONE
	# This expects the module fields to already exist
	# Note: any new module wrappers must have this exact argument list
	def __init__(self, module, fault_tolerance, debug_output):
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		self.module = module
		self.module_name = self.module.module_name
		self.module_description = self.module.module_description
	def __repr__(self):
		return "< loaded module with name : %s >" % self.module_name
	
class ModuleLoader:
	# Necessary attributes for a generic module
	# Subclasses may override this to provide for different required attributes
	necessary_attributes = ["module_name", "module_description"]
	necessary_attr_types = [str, str]
	# New classes should override the ModuleWrapper item
	ModuleWrapper = LoadedModule
	def __init__(self, path_list, fault_tolerance=True, debug_output=DEBUG_NONE):
	
		self.path_list = path_list
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance
		self.valid_modules = []
		self.execute_load()
	
	def __repr__(self):
		return "ModuleLoader(" + self.path_list + ", " + self.fault_tolerance + ", " + self.debug_output + ")"
	
	# There is another definition later.  Which do we want?
	#def __str__(self):		
	#	return "Module Loader:\nWrapper Type: " + str(type(self.ModuleWrapper)) + "\nNecessary Attributes: " + str(self.necessary_attributes) + "\nSearch Paths: " + str(self.path_list) + "\nLoaded modules: " + str(self.valid_modules) + "\nUsing fault tolerance: " + str(self.fault_tolerance) + "\nDebug Level: " + str(self.debug_output)
	
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
		return len(self,valid_modules)
			
	def __iter__(self):
		return ModuleLoaderIterator(self)	
		
	def execute_load(self):
		# Perform validation to ensure that we didn't end up invalid
		# parameters
		if type(self.path_list) is not list:
			raise ModuleLoaderInitException(MLOAD_NOT_LIST)
			
		# Only perform an actual import if we have a non-zero list
		if len(self.path_list) is not 0:
			# Perform validation of the content of the path_list					
			for p in self.path_list:
				if type(p) is not str:
				# Prune from list if not a string
					if self.fault_tolerance:
						self.path_list.remove(p)
					else:
						raise ModuleLoaderInitException(MLOAD_HAS_NONSTR)
					
			
			for path_name in self.path_list:
				loaded_directory = ModuleDirectoryScanner(path_name, self.fault_tolerance, self.debug_output)
				for loaded_module in loaded_directory:
					if self.validate_module(loaded_module):
						self.valid_modules.append(self.ModuleWrapper(loaded_module, self.fault_tolerance, self.debug_output))
								
		else:
			if not self.fault_tolerance:
				raise ModuleLoaderInitException(MLOAD_EMPTY_LIST)
				
	# Provide a string method
	def __str__(self):
		return "Module loader:\n" + repr(self.valid_modules	)
		
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
				print "Validating fields %s : %s" % (field, hasattr(module, field))
			if not hasattr(module, field):
				if not self.fault_tolerance:
					raise ModuleUnloadeableException(module.__name__, "Module does not have field %s" % field)
				else:
					return False
			ind = self.necessary_attributes.index(field)
			# This only runs when we have actually specified out to that
			# type
			if ind < self.necessary_attr_types:
				# Ahh ye olde debugging output, you take up so much space
				if self.debug_output >= DEBUG_ALL:
					print "Validating field %s as type %s : %s" % (field, self.necessary_attr_types[ind], type(module.__dict__[field]) == self.necessary_attr_types[ind] and self.necessary_attr_types[ind] is not None)
				
				if not type(module.__dict__[field]) == self.necessary_attr_types[ind] and self.necessary_attr_types[ind] is not None:
					if not self.fault_tolerance:
						raise ModuleUnloadeableException(module.__name__, "Module field %s was not of type %s" % ( field, self.necessary_attr_types[ind]))
					else:
						return False
		# If we get to the end, we were successful
		return True
	# Determine if the module has the necessary activation hooks to be
	# a module.  Subclasses will probably have to reimplement this method
	# from scratch, since a default module provides no hooks into the module
	# and simply returns true.  DEBUG output can be retrieved by simply chaining
	# up, since there is no
	def validate_additional(self, module):
		return True
		
	# This is not actually used by default, but is provided as a convenience,
	# so that base classes do not have to reimplement it
	def validate_execution_hook(self, module, name, num_args):
		if self.debug_output >= DEBUG_ALL:
			print "Module %s has attribute %s: %s " % (module, name, hasattr(module, name))
			print "Module attribute %s is of type 'func_code': %s" % (name, hasattr(module.__dict__[name], "func_code"))
			print "Module function %s has %d args: %s" % (name, num_args, module.__dict__[name].func_code.co_argcount is num_args)
		hasfunc = hasattr(module, name) 
		func_is_func = hasattr(module.__dict__[name], "func_code")
		func_has_correct_param = module.__dict__[name].func_code.co_argcount is num_args
		
		if not hasfunc and not self.fault_tolerance:
			raise ModuleUnloadeableException(module.__name__, "Module did not have attribute named %s" % name)
		if not func_is_func and not self.fault_tolerance:
			raise ModuleUnloadeableException(module.__name__, "Module attribute %s was not a function" % name)
		if not func_has_correct_param and not self.fault_tolerance:
			raise ModuleUnloadeableException(module.__name__, "Module function %s did not have %d arguments" % (name, num_args))
		# Ryan: Is this ok? 
		return True
	
	# Deprecated: Use mappings instead	
	def module(self, mod_name):	
		if self.debug_output >= DEBUG_ALL:
			print "Searching for module: %s" % mod_name	
		for x in self.valid_modules:
			if self.debug_output >= DEBUG_ALL:
				print "Looking at module: %s trying to find: %s" % (x, mod_name)
			if x.module_name == mod_name or x.module.__name__ == mod_name:
				return x
		return None


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

class ModuleDirectoryScanner:
	def __init__(self, path, fault_tolerance, debug_output):
		self.duplicate_path =  False
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		self.path = path
		
		if self.path not in sys.path:
			sys.path.append(self.path)
			if self.debug_output >= DEBUG_ALL:
				print "Adding %s to path list" % self.path
				print sys.path
				
			
		else:
			if self.debug_output >= DEBUG_ALL:
				print "Not adding %s to path list" % self.path
				print sys.path
			self.duplicate_path = True
		
		self.dir_modules = []
		if debug_output >= DEBUG_ALL:
			print "Scanning directory: %s" % self.path
		self.scan()
		self.load()
			
			
	def __iter__(self):
		return ModuleDirectoryScannerIterator(self)		
	
	# Scan for possible modules that can be loaded	
	def scan(self):
		if self.path[len(self.path) - 1] == '/':
			glob_pattern = self.path + "*.py"
		else:
			glob_pattern = self.path + "/*.py"
		found_modules = glob.glob(glob_pattern)
		# Remove the remaining path names from the module, since 
		# We also have to add 1 to the index of the /
		stripped_modules = [mod[mod.rfind("/") + 1:] for mod in found_modules if mod.rfind("/") != -1]
		non_stripped_modules = [mod for mod in found_modules if mod.rfind("/") == -1]
		self.found_modules = stripped_modules + non_stripped_modules
		
	# Load modules			
	def load(self):
		if self.debug_output >= DEBUG_ALL:
			print "Located all modules: %s" % self.found_modules
		for modname in self.found_modules:
			if self.debug_output >= DEBUG_ALL:
				print "Attempting to 'find' module: %s" % modname
			# This assumes that we always have .py extension.  Is this correct?
			stripped_modname = modname[0:modname.rfind(".py")]
			file_handle, filename, description = imp.find_module(stripped_modname)
			loaded_module = None
			if not file_handle:
				if self.debug_output >= DEBUG_ALL:
					print "Failed 'finding' module (programming error or possible collision with builtin module): %s" % stripped_modname
				if not self.fault_tolerance:
					raise ModuleUnloadeableException(stripped_modname, "Module could not be found by imp.find_module()")
			else:
				try:
					loaded_module = imp.load_module(stripped_modname, file_handle, modname, description)
				except:
					# Close our file handle
					file_handle.close()
					# If we are not using fault tolerance, reraise
					if not self.fault_tolerance:
						raise
					else:
						if self.debug_output >= DEBUG_ALL:
							print "Load failed on module: %s, attempting recovery" % stripped_modname
							print sys.exc_info()[0]
							
				file_handle.close()

				
			# If loaded module is None, something went wrong
			if loaded_module:
				self.dir_modules.append(loaded_module)
					
class ModuleDirectoryScannerIterator:
	def __init__(self, parent):
		self.parent = parent
		self.ind = -1
	def next(self):
		self.ind = self.ind + 1
		if self.ind == len(self.parent.dir_modules):
			raise StopIteration
		else:
			return self.parent.dir_modules[self.ind]
		
