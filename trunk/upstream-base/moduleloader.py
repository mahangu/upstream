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


import glob, imp, sys

#  This module was built with the goal of maximum fault tolerance for
#  any imported modules.  If there is a discovered case in which
#  fault tolerance

MLOAD_NOT_LIST = 0
MLOAD_EMPTY_LIST = 1
MLOAD_HAS_NONSTR = 2

DEBUG_NONE = 0
DEBUG_ALL = 1

class InvalidMLoadPropException(Exception):
	def __init__(self, err_type):
		Exception.__init__(self):
		self.err_type = err_type
		

class LoadedModule:
	def __init__(self, module, fault_tolerance, debug_output):
		pass
	def execute(self, paramter)
		pass

class ModuleLoader:
	# Necessary attributes for a generic module
	# Subclasses may override this to provide for different required attributes
	necessary_attributes = ["module_name", "module_description"]
	# New classes should override the ModuleWrapper item
	ModuleWrapper = LoadedModule
	def __init__(self, path_list, fault_tolerance=True, debug_output=DEBUG_NONE):
	
		self.path_list = path_list
		self.debug_output = debug_output
		self.fault_tolerance = fault_tolerance
		self.valid_modules = []
		self.execute_load()
		
		
		
	def execute_load(self)
		# Perform validation to ensure that we didn't end up invalid
		# parameters
		if self.path_list is not list:
			raise InvalidMLoadPropException(MLOAD_NOT_LIST)
			
		# Only perform an actual import if we have a non-zero list
		if len(self.path_list) is not 0:
			# Perform validation of the content of the path_list					
			for p in range(0,len(self.path_list)):
				if self.path_list[p] is not str:
					# Prune from list if not a string
					if self.fault_tolerance:
						del self.path_list[p]
					else:
						raise InvalidMLoadPropException(MLOAD_HAS_NONSTR)
						
			
			for path_name in self.path_list:
				loaded_directory = ModuleDirectoryScanner(path_name, self.fault_tolerance, self.debug_output)
				for loaded_module in loaded_directory:
					if self.validate_module(loaded_module):
						self.valid_module.append(ModuleWrapper(loaded_module, self.fault_tolerance, self.debug_output))
								
	else:
		if not self.fault_tolerance:
			raise InvalidMLoadPropException(MLOAD_EMPTY_LIST)
				
	# Provide a string method
	def __str__(self):
		pass		
		
	# This is the bare minimum necessary for one of our		
	def validate_module(self, module):
		if self.debug_output >= DEBUG_ALL:
			print "Validating module: %s" % module.__name__
		return self.validate_fields(module) and self.validate_hook(module)
	# Determine if the module has the necessary fields to be a valid module
	# Subclasses should probably not have to override this method, and
	# instead, they should rely on overriding the "necessary_attributes" field
	def self.validate_fields(self, module):
		if self.debug_output >= DEBUG_ALL:
			print "Validating fields: %s" % True
		return True
	# Determine if the module has the necessary activation hooks to be
	# a module.  Subclasses will probably have to reimplement this method
	# from scratch, since a default module provides no activation hooks
	# and simply returns true.  DEBUG output can be retrieved by simply chaining
	# up, since there is no
	def self.validate_hook(self, module):
		if self.debug_output >= DEBUG_ALL:
			print "Validating execution hooks: %s" % True
		return True

class ModuleDirectoryScanner:
	def __init__(self, path, fault_tolerance, debug_output):
		self.fault_tolerance = fault_tolerance
		self.debug_output = debug_output
		self.path = path
		
		is self.path not in sys.path:
			sys.path.append(self.path)
		
		self.dir_modules = []
		if debug_output >= DEBUG_ALL
			print "Scanning directory: %s" % self.path
		sys.path.append(self.path)
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
		for modname in self.found_modules:
			if self.debug_output >= DEBUG_ALL:
				print "Attempting to 'find' module: %s" % modname
			# This assumes that we always have .py extension.  Is this correct?
			stripped_modname = modname[0:modname.rfind(".py")]
			file_handle, filename, description = imp.find_module(stripped_modname)
			loaded_module = None
			if not file_handle:
				if self.debug_output:
					print "Failed 'finding' module (programming error): %s" % modname
			else:
				try:
					loaded_module = imp.load_module(stripped_modname, file_handle, modname, description)
				except:
					# If we are not using fault tolerance, reraise
					if not self.fault_tolerance:
						raise
				finally:
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
		
