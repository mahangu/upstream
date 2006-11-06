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

# Required by Generic Module
module_name = "xorgConf"
module_description = "Read the Xorg configuration file"
# Required by Log Module
log_path = "/etc/X11/xorg.conf"
category = "video"

def execute():
	try:
		fp = open(log_path, "r")
	except IOError:
		return module_name, "Could not open this log file!"
	else:
		content = fp.read()
		fp.close()
		return module_name, content
