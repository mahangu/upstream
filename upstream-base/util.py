#!/usr/bin/python
#
# utility functions for upstream
# Copyright (C) 2006
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.\

# submit modules
def flat_log(log_tuple):
	"""Put all the elements into one log"""
	flat_log = ""
	print log_tuple
	for (name, path, contents) in log_tuple:
		flat_log = flat_log + "\n\n%s (%s):\n%s" % (name, path, contents)
	print flat_log
	return flat_log

	
# Deprecated
def make_log_tuple(mod_list):
	log_list = []
	for module in mod_list:
		name = module.module_name
		path = module.log_path
		contents = module.execute()
		log_list.append((name, path, contents))
	return tuple(log_list)

# vim:set noexpandtab: 
