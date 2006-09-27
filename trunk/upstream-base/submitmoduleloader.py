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

import glob, imp

class ModuleDirDescription:
	def __init__(self, path):
		self.found_modules = []
		self.path = path
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
			return {"path":self.parent.path , "name":proper_module_name}
	

# Class that handles the loading of submission modules
class SubmitModuleLoader:
	# Intialize the full search path as empty
	def __init__(self):
		self.search_paths = []
		self.search_path_descriptor = []
		self.loaded_submit_modules = []
		
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
		print "Loading"
		for mod_path in self.search_path_descriptor:
			print "mod_path: %s" % (mod_path.path)
			for module in mod_path:
				print "module: %s" % module
				print "Loading module at: %s %s" % (module["path"], module["name"])
	
