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

import moduleloader, sys

unknown_response = """<html>
				<head>
					<title>Error Page!</title>
				</head>
				<body>
					<h3>The module returned an unreconized type</h3><br />
					<p>This is usually due to an incorrectly designed
					submission module.  You request may have succeeded,
					but the program has no way of determining this</p>
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
	def __init__(self, module, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.LoadedModule.__init__(self, module, fault_tolerance, debug_output)
		self.module_submit_url = self.module.module_submit_url
		
	def execute(self, email, message, log_dict):
		try:
   			res =  self.module.execute(email, message, log_dict)
   			# We are expecting a submit module result, take action if not found
			## We should consider:
			## http://www.python.org/download/releases/2.2.3/descrintro/
			## http://docs.python.org/ref/node33.html
   			#if type(res) == SubmitModuleResult:
   			if res.__class__ == SubmitModuleResult:
   				return res
   			else:
   				if self.debug_output >= moduleloader.DEBUG_ALL:
   					print "Module execute returned type %s expected %s" % (type(res), SubmitModuleResult)
   				if self.fault_tolerance:
   				 # We are using fault tolerance so try and send back a message to the user
   				 	return SubmitModuleResult(False, False, unknown_response)
   				else:
   				 	raise moduleloader.IncorrectModuleReturnType(type(res), type(SubmitModuleResult))
   		# Attempt to handle exceptions if we get one
    		except:
    			if self.debug_output >= moduleloader.DEBUG_ALL:
    				print "Error in execution of %s" % self.module_name
    				print sys.exc_info()[0]
    				
    			if self.fault_tolerance:
   				formatted_str = exception_template % (sys.exc_info()[0], self.module_name)
   				return SubmitModuleResult(False, False, formatted_str)
   			else:
   				raise
		
				
class SubmitModuleLoader(moduleloader.ModuleLoader):
	necessary_attributes = moduleloader.ModuleLoader.necessary_attributes + ["module_submit_url"]
	necessary_attr_types = moduleloader.ModuleLoader.necessary_attr_types + [str]
	ModuleWrapper = SubmitModule
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output)
		
	def validate_additional(self, module):
		valid_hook = self.validate_execution_hook(module, "execute", 3)
		return valid_hook
		
		


	
