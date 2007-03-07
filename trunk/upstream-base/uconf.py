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
import constants

# Deprecated
LOG = 0
SUBMIT = 1
# Replacements
INPUT = 0
OUTPUT = 1

base_path_default = constants.conf_dir

class PluginConfigReader:
	def __init__(self, plugin_type, base_path=base_path_default):
		self.__base_path = base_path
		self.__plugin_type = plugin_type
		self.__plugins_c = ConfigParser.ConfigParser()
		regex = re.compile(".*\.conf$")
		if plugin_type == LOG:
			for f_name in os.listdir(self.__base_path + "/log-plugins.d/"):
				if regex.match(f_name, 1):
					self.__plugins_c.read(self.__base_path + "/log-plugins.d/" + f_name)
		else:
			for f_name in os.listdir(self.__base_path + "/submit-plugins.d/"):
				if regex.match(f_name, 1):
					self.__plugins_c.read(self.__base_path + "/submit-plugins.d/" + f_name)
	# Deprecated
	def get_all_packages(self):
		return self.__plugins_c.sections()
	
	def get_packages(self):
		return self.__plugins_c.sections()			
			
	def get_plugin_md5(self, package, name):
		if self.__plugins_c.has_section(package):
			if self.__plugins_c.has_option(package, name):
				md5 = self.__plugins_c.get(package, name)
				return md5
		return None
		
	def get_md5(self, package, name, extension):
		if self.__plugins_c.has_section(package):
			if self.__plugins_c.has_option(package, name + "_" + extension):
				md5 = self.__plugins_c.get(package, name + "_" + extension)
				return md5		
		# We get through all the if's so we should return None
		return None	
		
	def get_base_path(self):
		return self.__base_path
	
	def get_plugin_type(self):
		return self.__plugin_type
	
	def get_plugin_type_str(self):
		if self.__plugin_type == LOG:
			return "input"
		else:
			return "outpu"
	
	# Deprecated
	def getbase_path(self):
		return self.__base_path
