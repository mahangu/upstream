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

import ConfigParser, os, re

LOG = 0
SUBMIT = 1

base_path_default = "../conf"

class PluginConfigReader:
	def __init__(self, p_type, base_path=base_path_default):
		self._base_path = base_path
		
		self._plugins_c = ConfigParser.ConfigParser()
		regex = re.compile(".*\.conf$")
		if p_type == LOG:
			for f_name in os.listdir(self._base_path + "/log-plugins.d/"):
				if regex.match(f_name, 1):
					self._plugins_c.read(self._base_path + "/log-plugins.d/" + f_name)
		else:
			for f_name in os.listdir(self._base_path + "/submit-plugins.d/"):
				if regex.match(f_name, 1):
					self._plugins_c.read(self._base_path + "/submit-plugins.d/" + f_name)
	
	def get_all_packages(self):
		return self._plugins_c.sections()
			
	def get_md5(self, package, name, extension):
		if self._plugins_c.has_section(package):
			print name + "_" + extension
			if self._plugins_c.has_option(package, name + "_" + extension):
				md5 = self._plugins_c.get(package, name + "_" + extension)
				return md5		
		# We get through all the if's so we should return None
		return None
	
	
		
	def getbase_path(self): return self._base_path
