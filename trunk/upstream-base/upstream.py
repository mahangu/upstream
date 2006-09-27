#!/usr/bin/python
#
# Upstream - log file aggregator and report tool for *nix systems.
# Copyright (C) 2006  Mahangu Weerasinghe (mahangu@gmail.com)
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

import sys, optparse, os, ConfigParser

import functions # our modules
functions.set_conf_dir("conf/")
functions.set_modules_dir("modules/")


parser = optparse.OptionParser("%prog yourname@yourdomain.org \"Your support message\" [options]")

for x in functions.get_conf_sections("list"):
		sflag = functions.get_conf_item("list", x, "sflag")
		lflag = functions.get_conf_item("list", x, "lflag")
		print sflag

		parser.add_option(sflag, lflag, action="store_true", help=functions.get_conf_item("list", x, "help"), default=False)

parser.add_option("", "--pastebin", dest="pastebin", help="Specify a pastebin module to use.", default=False)

(options, args) = parser.parse_args()

if options.pastebin:
	functions.read_module(options.pastebin)
	
else:
	functions.read_module()
	
	

for x in options.__dict__.iteritems():
	section = x[0]
	boolean = x[1]

	if boolean ==  1:
		log_path = functions.get_conf_item("list", section, "file")
		help = functions.get_conf_item("list", section, "help")
		dump = functions.get_log(log_path)
		response = functions.add_final(dump)


# Check to see if all mandatory arguments have been filled.


if len(args) != 2:
	print "Please specify the required options. See help (-h) for more information."
	sys.exit(1)


#  Populating final variables.

user_email = args[0]
user_message = args[1]

print user_message
print user_email

user_logs = functions.get_final()

response = functions.send_curl(user_logs, user_message, user_email)

print response
