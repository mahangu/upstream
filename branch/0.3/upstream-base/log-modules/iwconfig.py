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
module_name = "iwconfig"
module_description = "get iwconfig output"
# Required by Log Module
log_path = "/sbin/iwconfig"
category = ["network"]

# What happens if log_path does not exist or user does not have proper permissions?
def execute():
	if os.access(log_path, os.X_OK):
		p = os.popen(log_path, "r")
	else:
		return "Could not successfully execute %s!" % (log_path)
	content = p.read()
	p.close()
	# Potentially do some removing of sensetive info like ESSIDs?
	return content
