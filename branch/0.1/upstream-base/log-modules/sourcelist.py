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

# This module has to be sourceslist.py otherwise it will conflict with the builtin
# debian module called apt

# Required by Generic Module
module_name = "apt"
module_description = "Read the file used to control software repositories in Debian based systems"
# Required by Log Module
log_path = "/etc/apt/sources.list"
category = "apt"

def execute():
	try:
		fp = open(log_path, "r")
	except IOError:
		return module_name, "Could not open this log file!"
	else:
		#content = fp.readlines()
		#singlecontent = ""
		#for line in content:
		#	print line
		#	print singlecontent
		#	singlecontent = singlecontent + line
		#return module_name, singlecontent

		# Is this ok instead?
		content = fp.read()
		fp.close()
		return module_name, content
