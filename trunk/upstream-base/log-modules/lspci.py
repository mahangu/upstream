#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
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

import os

# Required by Generic Module
module_name = "lspci"
module_description = "Get lspci output"
# Required by Log Module
log_path = "/usr/bin/lspci"
category = "video"

# What happens if log_path does not exist or user does not have proper permissions?
def execute():
	#try:
	p = os.popen(log_path, "r")
	#except IOError:
		#return module_name, "Could not successfully execute %s!" % (log_path)
	#else:
	content = p.read()
	p.close()
	return module_name, content
