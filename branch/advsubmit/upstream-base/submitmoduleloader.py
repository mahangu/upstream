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

import moduleloader, sys, messageframe
		
class SubmitValidator(moduleloader.GenericValidator):
	necessary_attributes = moduleloader.GenericValidator.necessary_attributes + ["module_submit_url"]
	necessary_attr_types = moduleloader.GenericValidator.necessary_attr_types + [str]
	ModuleWrapper = SubmitModule
	def __init__(self, parent, plugin_conf, fault_tolerance, debug_output):
		moduleloader.GenericValidator.__init__(self, parent, plugin_conf, fault_tolerance, debug_output)
	
	def validate_additional(self, module):
		valid_hook = self.validate_execution_hook(module, "execute", 3)
		return valid_hook
			
class SubmitModuleLoader(moduleloader.ModuleLoader):
	ValidatorClass = SubmitValidator
	ModuleWrapper = SubmitModule
	def __init__(self, path_list, fault_tolerance=True, debug_output=moduleloader.DEBUG_NONE):
		moduleloader.ModuleLoader.__init__(self, path_list, fault_tolerance, debug_output)	
