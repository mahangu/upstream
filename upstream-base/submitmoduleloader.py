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

import glob, imp, sys

class SubmitModuleResult:
	def __init__(self, bool_ispaste, bool_success, result_url=None, result_xml=None):
		self.bool_ispaste = bool_ispaste
		self.bool_success = bool_success
		self.result_url = result_url
		self.result_xml = result_xml
		

class ModuleDirDescription:
	def __init__(self, path):
		# We need to add the module to the searchpath apparently
		self.path = path
		sys.path.append(self.path)
		self.found_modules = []		
		self.scan()
	def __iter__(self):
		return ModuleDirIterator(self)		
	def scan(self):
		print "Scanning: Single path"
		if self.path[len(self.path) - 1] == '/':
			glob_pattern = self.path + "*.py"
		else:
			glob_pattern = self.path + "/*.py"
		found_modules = glob.glob(glob_pattern)
		# This may not be necessary
		# We also have to add 1 to the index of the /
		stripped_modules = [ mod[mod.rfind("/") + 1:] for mod in found_modules if mod.rfind("/") != -1]
		non_stripped_modules = [ mod[mod.rfind("/") + 1:] for mod in found_modules if mod.rfind("/") == -1]
		self.found_modules = stripped_modules + non_stripped_modules
				
			
class ModuleDirIterator:
	def __init__(self, parent):
		self.parent = parent
		self.ind = -1
	def next(self):
		self.ind = self.ind + 1
		if self.ind == len(self.parent.found_modules):
			raise StopIteration
		else:
			# The found modules should always end in .py so no big deal here
			# We are getting from the frnot of the found module name until the .py
			proper_module_name = self.parent.found_modules[self.ind][0:self.parent.found_modules[self.ind].rfind(".py")]
			# The fullname should be the proper_module_name + .py that was removed
			return {"path":self.parent.path , "name":proper_module_name, "fullname":proper_module_name + ".py"}


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
		
# A class that wraps around a loaded submit module
# it assumes that the module it is given is correctly formed	
class SubmitModule:
	def __init__(self, fault_tolerance, module):
		self.fault_tolerance = fault_tolerance
		self.module = module
		self.module_name = module.module_name
		self.module_description = module.module_description
		self.module_submit_url = module.module_submit_url
		
	def execute(self, email, support, dict_of_log):
		try:
			res =  self.module.execute(email, support, dict_of_log)
			return res
		except:
			print "Error in execution of %s" % self.module_name
			print sys.exc_info()[0]
			if self.fault_tolerance:
				formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
				return SubmitModuleResult(False, False, None, formatted_str)
			else:
				raise
				
	

# Class that handles the loading of submission modules
class SubmitModuleLoader:
	# Intialize the full search path as empty
	# If fault_tolerance = False, any exception raised by
	# this submit module loader or any SubmitModules retreived
	# by it will be handled, information printed, and then then exceptions
	# will be reraised
	def __init__(self, fault_tolerance=True):
		self.search_paths = []
		self.search_path_descriptor = []
		self.loaded_submit_modules = []
		self.fault_tolerance = fault_tolerance
		
	# Add a search  path to look for submission modules
	def add_search_path(self, path):
		if path and path not in self.search_paths:
			print "Adding paths"		
			self.search_paths.append(path)
			self.search_path_descriptor = [ ModuleDirDescription(path) for path in self.search_paths] 
			print "Total path list:\n%s" % self.search_path_descriptor
			
		if self.search_path_descriptor:			
			self.load()
		
	# Perform the necessary work to load modules
	# This should be considered a private method, although, unlike
	# scan, this could be used to force reloading all modules that
	# are already found
	def load(self):
		CONST_FILE_IND = 0;
		CONST_PATH_IND = 1
		CONST_DESC_IND = 2
		self.loaded_submit_modules = []
		for mod_path in self.search_path_descriptor:
			for module in mod_path:
				module_desc = imp.find_module(module["name"])
				# Catch any exceptions thrown by loading the module
				try:
					print "Attempting to load module: %s" % module["name"]
					loaded_module = imp.load_module(module["name"], module_desc[CONST_FILE_IND], module_desc[CONST_PATH_IND], module_desc[CONST_DESC_IND])
					if self.validate_module(loaded_module):
						new_mod = SubmitModule(self.fault_tolerance,loaded_module)
						self.loaded_submit_modules.append(new_mod)
						print "Successfully loaded module: %s" % module["name"]
					else:
						print "Skipping malformed module: %s" % module["name"]
				except:
					print "Module loading threw exception: %s" % module["name"]
					print sys.exc_info()[0]
					# Stub should always be valid
					if not self.fault_tolerance:
						raise
				
	# Perform the work necessary to validate a module as correctly formed
	def validate_module(self, module):
		if "module_name" in dir(module) and "module_description" in dir(module) and "module_submit_url" in dir(module) and "execute" in dir(module):
			return True
		else:
			return False
			
	def get_all_submit_modules(self):
		return [mod for mod in self.loaded_submit_modules]
		
	def get_module_by_name(self, name):
		for mod_object in self.loaded_submit_modules:
			print mod_object.module_name
			print mod_object.module.__name__
			if mod_object.module_name == name or mod_object.module.__name__ == name:
				return mod_object
		return None
	
